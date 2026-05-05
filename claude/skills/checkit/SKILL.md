---
name: checkit
description: Use when verifying that a builder agent's actual code changes match a peep contract's specification. Audits a diff against the archived contract via adversarial gap analysis: identifies unsatisfied requirements, violated invariants, scope creep; runs proofshot mandatorily for UI-behavior-affecting features; emits a structured verdict (PASS, GAP, BEHAVIORAL_FAIL, MANIFEST_INCOMPLETE) and a corrective prompt for the next builder session. Triggers include "checkit", "verify the build", "audit the diff", "did the builder ship what was specified", "verify peep-XXXXXXXX", "/checkit peep-XXXXXXXX". Pairs with peep — peep specifies, checkit verifies. Reads from the orphan branch `peep` archive at ~/peep-archive/<peepID>/ and writes verification runs back to the same archive.
---

# checkit — Forensic Verifier for peep Contracts

## Purpose

`peep` produces a contract at *plan time*. The builder ships code at *build
time*. **checkit closes the loop at audit time**: given a `peepID`, it audits
the actual code diff against the archived contract and emits a structured
verdict + corrective prompt. Every verification run is itself archived to the
same orphan branch as the contract, so the GitHub history is a permanent,
diffable trail joining every contract to every audit of it.

**This is not blind verification.** Adversarial framing of one agent
("find requirements that are NOT satisfied") is the bias mitigation, not a
sealed sandbox. If you want true blind reconstruction, that's a future
hardening — see "Honest limitations" below.

## Invocation

```
/checkit <peepID>
```

The peepID is **mandatory**, format `peep-<8 hex chars>`. No mtime fallback,
no auto-detect. The contract must already be archived at
`~/peep-archive/<peepID>/`.

## The four verdict tokens

Strict precedence — earliest match wins:

1. **`MANIFEST_INCOMPLETE`** — `build-manifest.json` missing required fields
2. **`BEHAVIORAL_FAIL`** — `proofshot` caught a regression (only possible
   when contract `UI_BEHAVIOR_AFFECTING=yes`)
3. **`GAP`** — gap-report.md found any NOT SATISFIED requirement, VIOLATED
   invariant, or scope creep
4. **`PASS`** — everything above clean

`corrective-prompt.md` is written for any non-PASS verdict.

## Inputs

Read from the archive:

| File | Purpose | Required |
|---|---|---|
| `~/peep-archive/<peepID>/contract.md` | the spec to verify against | yes |
| `~/peep-archive/<peepID>/build-manifest.json` | where the code change lives | yes |
| `~/peep-archive/<peepID>/mental-model.brief.md` | architectural intent (for adversarial agent context) | optional |
| `~/peep-archive/<peepID>/mental-model.png` | architectural intent (for adversarial agent context) | optional |

`build-manifest.json` schema:

```json
{
  "peepID": "peep-bbfa2319",
  "repo": "/abs/path/to/project",
  "base": "<git commit SHA before the change>",
  "head": "<git commit SHA after the change, or 'HEAD'>",
  "tests": ["pytest tests/test_foo.py::test_bar", ...],
  "app": { "launch_cmd": "...", "url": "http://localhost:..." }
}
```

`app.launch_cmd` and `app.url` are **required if and only if**
`contract.UI_BEHAVIOR_AFFECTING == yes`. If the field is `yes` and
`app.*` is absent → verdict = `MANIFEST_INCOMPLETE`.

## Workflow

### Step 1 — Validate inputs and create the run directory

```bash
PEEPID="$1"   # e.g. peep-bbfa2319
ARCHIVE=~/peep-archive/$PEEPID

# Validate
[ -f "$ARCHIVE/contract.md" ]          || { echo "no contract for $PEEPID" >&2; exit 2; }
[ -f "$ARCHIVE/build-manifest.json" ]  || { 
  RUN=$ARCHIVE/checkit/run-$(date -u +%Y-%m-%dT%H%MZ)-$(uuidgen | cut -c1-6)
  mkdir -p "$RUN"
  echo "MANIFEST_INCOMPLETE" > "$RUN/verdict.md"
  cat > "$RUN/corrective-prompt.md" <<EOF
build-manifest.json is missing at $ARCHIVE/build-manifest.json. Builder must
write {peepID, repo, base, head, tests, app(if UI)} and re-run /checkit $PEEPID.
EOF
  # commit + push (Step 6) then exit
}

RUN="$ARCHIVE/checkit/run-$(date -u +%Y-%m-%dT%H%MZ)-$(uuidgen | cut -c1-6)"
mkdir -p "$RUN"
```

### Step 2 — Compute the diff

```bash
REPO=$(jq -r .repo "$ARCHIVE/build-manifest.json")
BASE=$(jq -r .base "$ARCHIVE/build-manifest.json")
HEAD=$(jq -r .head "$ARCHIVE/build-manifest.json")
git -C "$REPO" diff "$BASE..$HEAD" > "$RUN/diff.txt"
```

If the diff is huge (>2 MB), truncate with a header noting the truncation.
`git diff` already skips binaries (replaced with `Binary files differ`).

### Step 3 — Adversarial gap analysis (mandatory)

Dispatch one `hephaestus` call using `templates/adversarial-audit.md` as the
brief. Substitute the placeholder paths with the actual `$ARCHIVE` and `$RUN`
values. Hephaestus reads `contract.md` and `diff.txt` and produces
`$RUN/gap-report.md`.

```bash
brief=$(mktemp)
sed -e "s|{{ARCHIVE}}|$ARCHIVE|g" -e "s|{{RUN}}|$RUN|g" -e "s|{{PEEPID}}|$PEEPID|g" \
  /home/david/.claude/skills/checkit/templates/adversarial-audit.md > "$brief"

COMPLETION_GUARD_TASK_TYPE=gap_analysis \
HEPHAESTUS_MODEL=gpt-5.5 HEPHAESTUS_REASONING_EFFORT=high \
hephaestus --file "$brief" --dir "$RUN" --dangerous
```

Wait for `gap-report.md` to land. Read its closing line:
- `GAP_FINDINGS_FOUND` → verdict candidate `GAP`
- `GAP_FINDINGS_NONE` → verdict candidate `PASS`

### Step 4 — Proofshot (mandatory if UI-affecting)

```bash
UI=$(grep -E "^UI_BEHAVIOR_AFFECTING:" "$ARCHIVE/contract.md" | awk '{print $2}')
if [ "$UI" = "yes" ]; then
  LAUNCH=$(jq -r '.app.launch_cmd // ""' "$ARCHIVE/build-manifest.json")
  URL=$(jq -r '.app.url // ""' "$ARCHIVE/build-manifest.json")
  if [ -z "$LAUNCH" ] || [ -z "$URL" ]; then
    echo "MANIFEST_INCOMPLETE" > "$RUN/verdict.md"
    cat > "$RUN/missing-proofshot-fields.md" <<EOF
Contract declares UI_BEHAVIOR_AFFECTING=yes but build-manifest.json is missing
app.launch_cmd or app.url. Builder must fill these and re-run /checkit $PEEPID.
EOF
    cat > "$RUN/corrective-prompt.md" <<EOF
$(cat "$RUN/missing-proofshot-fields.md")
EOF
    # skip to commit + push
  else
    mkdir -p "$RUN/proofshot"
    # invoke /proofshot with the contract's UI NEW_TEST_OBLIGATIONS as the
    # test plan, $LAUNCH as the launch command, $URL as the target.
    # Save artifacts to $RUN/proofshot/.
    # If proofshot reports any failure, set verdict candidate = BEHAVIORAL_FAIL.
  fi
fi
```

When invoking `/proofshot`, pass:
- `--launch`: the launch command from the manifest
- `--url`: the URL from the manifest
- `--scenarios`: file containing the contract's UI-related NEW TEST OBLIGATIONS (NTn rows where the test exercises a UI flow), one per line
- `--out`: `$RUN/proofshot/`

A proofshot failure (timeout, console error, visual regression, failed
assertion) → `BEHAVIORAL_FAIL` candidate.

### Step 5 — Apply verdict precedence

```python
if MANIFEST_INCOMPLETE_set:    verdict = "MANIFEST_INCOMPLETE"
elif BEHAVIORAL_FAIL_set:      verdict = "BEHAVIORAL_FAIL"
elif GAP_set:                  verdict = "GAP"
else:                          verdict = "PASS"
```

Write verdict.md (single token on first line):
```bash
echo "$VERDICT" > "$RUN/verdict.md"
```

### Step 6 — Corrective prompt (any non-PASS)

If verdict is not `PASS`, write `$RUN/corrective-prompt.md` containing:

- The verdict token
- Bulleted list of every NOT-SATISFIED Rn, VIOLATED INVm, scope-creep file,
  proofshot failure, or missing manifest field
- For each, what the builder should do next (file edits, missing tests,
  missing manifest field, etc.)

This file is the input to the next builder session.

### Step 7 — Commit + push the orphan branch

```bash
cd ~/peep-archive
git add "$PEEPID/checkit/$(basename "$RUN")"
git commit -m "checkit $PEEPID verdict=$VERDICT"
for i in 1 2 3; do
  git pull --rebase origin peep && git push origin peep && break
  sleep 2
done
```

### Step 8 — Report to the user

Print:
```
checkit complete: <peepID>
  run:     <run path>
  verdict: <verdict token>
  pushed:  origin/peep
  next:    <if non-PASS>: read $RUN/corrective-prompt.md, fix, re-run /checkit
           <if PASS>:     ship it
```

## Run folder naming

`<run> = ~/peep-archive/<peepID>/checkit/run-<UTC-iso>-<6char-uuid>/`

Example: `~/peep-archive/peep-bbfa2319/checkit/run-2026-05-05T0142Z-3f9a2c/`

No counter — race-free under concurrent checkit invocations.

## Outputs in the run folder

| File | When | Contents |
|---|---|---|
| `diff.txt` | always | the audited diff |
| `gap-report.md` | always (unless MANIFEST_INCOMPLETE before Step 3) | adversarial review findings |
| `verdict.md` | always | one token: PASS \| GAP \| BEHAVIORAL_FAIL \| MANIFEST_INCOMPLETE |
| `corrective-prompt.md` | non-PASS | next-builder-session instructions |
| `proofshot/` | UI-affecting + manifest complete | proofshot session artifacts |
| `missing-proofshot-fields.md` | UI-affecting + manifest incomplete | what fields are missing |

## Honest limitations

- **Not blind.** The adversarial agent has the contract while reviewing the
  diff. Adversarial framing ("find requirements that are NOT satisfied") is
  the only bias mitigation. The previous design's "sealed temp dir" was
  policy not enforcement on this machine because hephaestus runs codex with
  `--dangerously-bypass-approvals-and-sandbox`. True blind reconstruction
  is a v2 hardening (requires bwrap or container isolation around the
  phase-1 dispatch); explicitly out of scope for v1.
- **Manifest is documentation, not enforcement.** If the builder lies in
  build-manifest.json (wrong base/head/repo), checkit audits the lie. Fix
  is builder discipline + clear peep template guidance, not checkit
  machinery.
- **Diff filtering is naive.** Huge diffs are truncated; binaries skipped
  by git itself; generated files are NOT auto-excluded — that's the
  builder's responsibility via `.gitattributes`.

## See also

- `peep` — produces the contracts checkit verifies
- `proofshot` — invoked by checkit for UI-affecting features
- `hephaestus` — the deep worker checkit dispatches for adversarial review
- Orphan branch `peep` of `david-kijko/david-harness` — the archive of all contracts and verifications
