# Template: Brownfield Feature Construction

**Use when**: adding a feature to an EXISTING codebase. The project has files, callers, tests, conventions, deprecated patterns you may not know about, and invariants you can violate by accident. The dominant uncertainty is *existing-system uncertainty*.

**Failure modes this template guards against** (full catalog with citations in `references/failure-modes.md`):

| # | Mode | What goes wrong |
|---|---|---|
| B1 | Pattern reinvention | Building a parallel implementation of something that already exists in the repo |
| B2 | Deprecated-pattern reuse | Copying a pattern that still exists but the team is phasing out |
| B3 | Invariant violation | Breaking an implicit assumption the surrounding code depends on |
| B4 | Scope creep / over-refinement | Touching files that have no requirement attached to them |
| B5 | Spec drift | Building what you imagined, not what was asked |
| B6 | Integration mismatch | New code works in isolation but doesn't connect to actual callers |
| B7 | Regression in existing tests | Change passes new tests but silently breaks PASS_TO_PASS coverage |

Empirical context: studies show LLM agents introduce breaking changes during maintenance/refactor at rates of **6.72%–9.35%** per task, and ~75% of agents break previously-working code at least once per maintenance loop (see `references/failure-modes.md` for citations). Brownfield construction is where most damage actually happens.

This template is an *informal correct-by-construction certificate*: spec → implementation plan → discharge of proof obligations. See `references/refinement-vocabulary.md` for the formal vocabulary (Dijkstra wp/sp, design-by-contract, refinement, over-refinement). For the hypothesis-driven exploration loop used in EXISTING PATTERN SURVEY, see `references/exploration-loop.md`. For tagging each CLAIM by inference type, see `references/claim-types.md`.

---

## Fill the certificate. Read the codebase. Cite `file:line`.

```
SEMI-FORMAL BROWNFIELD CONSTRUCTION CERTIFICATE

DEFINITIONS
D1: SUFFICIENT iff every Rn has at least one mapped change in CHANGE SURFACE
    AND at least one demonstrating NTn in NEW TEST OBLIGATIONS.
D2: MINIMAL iff every row in CHANGE SURFACE cites at least one Rn (no
    over-refinement; no file changed without a requirement attached).
D3: COMPATIBLE iff every existing caller in BACKWARD-COMPATIBILITY TRACE
    is preserved or its breakage is explicitly justified, AND every
    PASS_TO_PASS test on the change surface remains green by trace.
D4: VERIFIABLE iff every Rn maps to at least one NTn whose pass/fail can
    be observed by running a concrete command.

SPEC (verbatim from the user — do not paraphrase)
[Paste the requirement exactly as given.]

SPEC DECOMPOSITION (atomic, testable)
R1: [single requirement]
R2: [single requirement]
...
(Anything not listed here is OUT OF SCOPE. If the user's words allow
multiple readings, list each Rn variant and flag the ambiguity rather
than picking silently.)

EXISTING PATTERN SURVEY  (mandatory — guards B1, B2)
For each concern the feature touches, run a hypothesis-driven search.
(Use the exploration loop in `references/exploration-loop.md` if needed:
H1, H2, H3 with confidence updates.)

| Concern | Hypothesis: pattern exists? | Evidence (file:line) | Still preferred? | Decision |
|---|---|---|---|---|
| [auth, retry, cache, ...] | [yes/no/unsure] | [file:line or "searched X, found nothing"] | [yes/no/deprecated/unknown] | [REUSE / EXTEND / NEW + justification] |

(NEW chosen when REUSE was possible MUST cite why the existing pattern is
insufficient. REUSE chosen when the pattern is deprecated MUST cite the
replacement. Treat these as proof obligations, not preferences.)

INTEGRATION POINTS  (where new code touches existing code)
IP1: [file:line] — [caller / callee / shared state] — [what changes here]
IP2: [file:line] — [...] — [...]

INVARIANTS THAT MUST BE PRESERVED  (guards B3)
INV1: [property the existing system maintains, e.g. "every User row has a
       non-null tenant_id"] — Evidence: [file:line where this is established
       or relied upon]
       Why this change preserves it: [trace or proof obligation discharged]
INV2: [...] — Evidence: [...] — Why preserved: [...]

CHANGE SURFACE  (every file that changes — guards B4 via D2)
| File | New / Modified | Approx lines | Discharges Rn |
|---|---|---|---|
| ... | ... | ... | R1, R3 |

(EVERY row MUST cite at least one Rn. A row with no Rn is over-refinement
and must be removed or a new Rn declared.)

REQUIREMENT → CODE MAPPING  (guards B5 via D1)
R1 → satisfied by [file:line(s)] because [trace from input to observable
     behavior]; inference type: [spec-decomposition / pattern-reuse /
     invariant-preservation / new-construction] (see `references/claim-types.md`)
R2 → satisfied by [file:line(s)] because [trace]; inference type: [...]
...
(EVERY Rn MUST appear here. If any Rn has no mapping, the plan is incomplete.)

BACKWARD-COMPATIBILITY TRACE  (guards B6, B7 via D3)
Existing callers of changed code:
  C1: [file:line] calls [function] expecting [behavior].
      After change: [STILL SATISFIED / BREAKING + migration plan]
  C2: ...
Existing tests touching the change surface (PASS_TO_PASS):
  T1: [test:line] — [STILL PASSES because trace] / [MUST UPDATE because
       spec change, new assertion: ...]
  T2: ...

NEW TEST OBLIGATIONS  (guards D4)
NT1: [test name] — Demonstrates R1 by [scenario → expected behavior]
     — Runnable command: [pytest path::name / npm test -- file]
NT2: [test name] — Demonstrates R2 by [scenario → expected behavior] — Runnable: [...]
...
(EVERY Rn MUST have at least one NTn.)

COUNTEREXAMPLE / SUFFICIENCY CHECK  (per-Rn binary)
For each Rn, exhibit ONE of:
  (a) Soundness sketch: state Rn as a property P(input). Argue ∀input. P(input)
      holds for the planned code, citing the file:line(s) where the property
      is enforced.
  (b) Concrete counterexample: an input or scenario where the planned code
      fails to satisfy Rn. Then either (i) revise the plan, or (ii) declare
      the case OUT OF SCOPE and amend the SPEC DECOMPOSITION.

R1 → [(a) sketch / (b) counterexample → response]
R2 → [...]

(Coverage check: which input partitions does NT1...NTn together exercise?
Note any unexercised partition that Rn implicitly requires.)

UI_BEHAVIOR_AFFECTING: [yes | no]
  Answer "yes" if any Rn changes the visible or interactive behavior of a
  GUI application (web page, desktop UI, mobile app, IDE plugin, browser
  extension, etc.). Answer "no" for pure backend, CLI, library, or
  build-tooling features.

  If "yes", NEW TEST OBLIGATIONS MUST include at least one UI flow
  describable as a proofshot scenario (start app -> navigate -> assert
  visual state), AND the builder MUST include `app.launch_cmd` and
  `app.url` in build-manifest.json before invoking checkit. checkit
  rejects MANIFEST_INCOMPLETE otherwise.

FORMAL CONCLUSION
By D1 (SUFFICIENT): [yes/no — every Rn has a mapping AND an NTn]
By D2 (MINIMAL):    [yes/no — every CHANGE SURFACE row cites an Rn]
By D3 (COMPATIBLE): [yes/no — every Cn preserved or justified; PASS_TO_PASS green]
By D4 (VERIFIABLE): [yes/no — every Rn has a runnable NTn]

Plan is READY TO IMPLEMENT: [YES / NO — if NO, list what's missing]
```

## MENTAL MODEL DIAGRAM (mandatory deliverable — produced AFTER the certificate)

The certificate captures your reasoning discipline. It does NOT capture your *mental model* — the architectural intuitions you carry that the prose left implicit (which existing-code boundaries you cross, which invariants flow through which call sites, which existing files own which concerns, what visual vocabulary distinguishes "owned by us" from "owned by upstream"). The diagram forces you to articulate them.

**Write the imagegen brief in YOUR OWN WORDS**, as if explaining the architecture to a fresh listener who has never seen your certificate or the existing codebase. The act of explaining surfaces assumptions you skipped, naming choices you internalized, integration shapes you assumed without stating, and relationships you took as obvious. **Do NOT copy from the certificate verbatim** — restate in fresh language. **Do NOT have anyone else write the brief for you** — the brief reveals what *you* consider salient about how the change fits the existing system.

The brief is the primary artifact. The image is its rendering. An adversarial reviewer will read the brief AND look at the image to spot business-logic errors, broken invariants, missing integration points, scope creep, or pattern misuse that the prose hid.

Decide for yourself:
1. What a fresh listener would need to understand BOTH the existing structure AND the change you're adding.
2. Which integration points, callers, invariants, contracts, and data flows are essential to convey.
3. What visual vocabulary distinguishes the categories you actually carry — modified vs new vs untouched, owned by you vs by upstream, preserved invariants vs newly-established ones, in-scope vs explicitly out-of-scope, deprecated patterns being avoided vs canonical ones being reused.
4. **INVARIANTS THE PICTURE MUST ENCODE** — claims that, if absent, make the diagram wrong (e.g. "the new helper MUST show the canonical retry import, not the deprecated one", "every existing caller box must have a still-satisfied tag", "the change surface boundary box must enclose ONLY files cited in CHANGE SURFACE — no others").
5. **WHAT THE PICTURE MUST NOT IMPLY** — anti-claims that prevent the image generator from inventing connections that aren't there (e.g. "no edits to legacy_retry.py", "no migration of FooClient — that's ticket #4421", "no new top-level package — the change lives inside the existing `clients/` module").

Save:
- Brief: `<output-dir>/mental-model.brief.md`
- Image: `<output-dir>/mental-model.png`

Render via Codex's built-in `$imagegen` skill (`cat /home/david/.codex/skills/imagegen/SKILL.md`).

Sections 4 and 5 above are the adversarial-review surface. Skipping them defeats the entire purpose of the diagram as a separate deliverable from the prose.

## SELF-ARCHIVE (v2.3 — mandatory closing step)

After FORMAL CONCLUSION and MENTAL MODEL DIAGRAM are complete, archive the contract to the orphan branch `peep` of `david-kijko/david-harness`. This makes the contract verifiable by `checkit` and any future reviewer, and is the durable audit trail that joins every contract to every verification of it.

### Step 1 — Compute peepID

```bash
PEEPID="peep-$(printf '%s' "$VERBATIM_SPEC" | sha256sum | cut -c1-8)"
```

`$VERBATIM_SPEC` MUST be the byte-exact user request you pasted into the SPEC field above. Same SPEC -> same peepID -> same archive folder (idempotent re-run).

### Step 2 — Bootstrap archive worktree (first use only)

If `~/peep-archive` does not exist on this machine:

```bash
cd ~/david-harness
git fetch origin peep:peep 2>/dev/null || (
  # Orphan branch not yet on remote either — create it
  tmpdir=$(mktemp -d)
  git worktree add --detach "$tmpdir"
  cd "$tmpdir"
  git checkout --orphan peep
  git rm -rf .
  printf '# peep archive\n\nOrphan branch storing peep contracts and checkit verification runs.\n' > README.md
  git add README.md
  git -c user.email="$(git config user.email)" -c user.name="$(git config user.name)" commit -m "init orphan branch peep"
  cd ~/david-harness && git worktree remove "$tmpdir" && git push -u origin peep
)
git worktree add ~/peep-archive peep
```

### Step 3 — Collision check, then write archive folder

```bash
ARCHIVE=~/peep-archive/$PEEPID
if [ -f "$ARCHIVE/spec.txt" ]; then
  if ! diff -q <(printf '%s' "$VERBATIM_SPEC") "$ARCHIVE/spec.txt" >/dev/null; then
    echo "sha8 collision at $PEEPID — extending to sha12" >&2
    PEEPID="peep-$(printf '%s' "$VERBATIM_SPEC" | sha256sum | cut -c1-12)"
    ARCHIVE=~/peep-archive/$PEEPID
  fi
fi

mkdir -p "$ARCHIVE"
printf '%s' "$VERBATIM_SPEC" > "$ARCHIVE/spec.txt"
# Write contract.md (the filled certificate above, less this SELF-ARCHIVE section)
# Write mental-model.brief.md (the brief authored under MENTAL MODEL DIAGRAM)
# Write mental-model.png (the rendered image)
```

### Step 4 — Commit + push

```bash
cd ~/peep-archive
git add "$PEEPID/"
git commit -m "$PEEPID: <one-line summary of the SPEC>"
for i in 1 2 3; do
  git pull --rebase origin peep && git push origin peep && break
  sleep 2
done
```

### Step 5 — Builder handoff (print to user)

Print:

```
peep contract archived: <peepID>
  archive: ~/peep-archive/<peepID>/
  branch:  peep (in david-kijko/david-harness)
  next:
    1. Builder reads ~/peep-archive/<peepID>/contract.md
    2. Builder modifies code in their project repo
    3. Builder writes ~/peep-archive/<peepID>/build-manifest.json:
         {peepID, repo, base, head, tests[], app:{launch_cmd,url} (if UI=yes)}
    4. Builder commits + pushes the manifest to orphan branch peep
    5. Run /checkit <peepID> to verify
```

If `UI_BEHAVIOR_AFFECTING=yes`, the builder MUST populate `app.launch_cmd` and `app.url` or checkit will return `MANIFEST_INCOMPLETE`.

## Common slip: filling the survey table from memory

The Existing Pattern Survey only works if you actually grep. "Hypothesis: there's probably a retry helper" without searching counts as zero evidence. Use the loop in `references/exploration-loop.md` — every hypothesis must be CONFIRMED or REFUTED by file:line evidence, with a confidence update.

## Common slip: writing "n/a" for invariants

If you genuinely cannot identify any invariant the change touches, you probably haven't read enough of the surrounding code. Read the type definitions, the schema, the constructors, the validation layer. "No invariants" in a brownfield project is almost always wrong.

## Common slip: skipping the counterexample on Rn that "obviously work"

The paper's failure mode 3 ("dismissing subtle differences") applies here too: if you wave your hand past sufficiency on R3 because it "just stores a value", you'll miss the case where the value shadows a pre-existing key. Force the soundness sketch or the counterexample for *every* Rn.

## Tone

Skip prose recap. Open straight to `SEMI-FORMAL BROWNFIELD CONSTRUCTION CERTIFICATE` and fill it.
