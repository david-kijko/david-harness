---
name: triage2
description: 'Use when a known, identified defect in an existing brownfield repo needs to be root-caused and fixed — "X is broken, find the root cause and fix it", "triage this bug", "/triage2", "the ingest preview is broken", "diagnose why Y fails and ship a fix". Use when the pathology may be non-obvious and warrants several parallel diagnostic angles before committing to a fix. NOT for greenfield builds, new features, or read-only Q&A about a codebase.'
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Skill
  - Workflow
  - AskUserQuestion
  - TodoWrite
  - Monitor
---

# triage — Deterministic Root-Cause-and-Fix for Brownfield Bugs

## Overview

`triage` fixes one **already-identified** defect in an existing repo. The orchestration is **deterministic**: a single `Workflow` script encodes the fan-out, the barrier, and the order of operations so the control flow never depends on model whim. The script — not prose — **enforces the load-bearing gates**: exa at low confidence (re-dispatch + exclude), `proofshot` when UI-affecting, credentials present before verify, the repo-identity misfile guard, and `status: FIXED` returned **only when verification actually passes**. This Claude session **orchestrates only** — every diagnostic deep-dive and the actual code fix are authored by **heph2 (gpt-5.5 high Codex)**.

**Core loop:** characterize → fan out N parallel heph2 diagnostic lanes (because pathology may be non-obvious) → synthesize the best-supported root cause → heph2 fix in an isolated worktree → proofshot the running app → register a Gotcha → merge to the active branch → offer cleanup.

## When to use / when NOT

Use when: a bug is reproducible or at least describable, the repo is brownfield, and you want several independent root-cause hypotheses pressure-tested before a fix lands.

Do NOT use for: building new features (use `forge`/`Simplement`), pure architectural Q&A (use `hypervisa-targeted-queries` / `repowise`), or trivial one-line fixes you can verify by eye.

## Role split (HARD)

- **Claude (this session, orchestrator):** collects inputs + credentials, authors the `Workflow` script and the heph2 briefs, runs the verification gate with literal stdout, merges, asks about cleanup. **Never writes the production fix itself.**
- **heph2 (gpt-5.5 high Codex):** ALL diagnostic investigation and ALL code edits. Dispatched from inside Workflow lanes via the `hephaestus` CLI.
- **exa CLI:** the research lane heph2 is **required** to call when its confidence in the root cause or fix is low.
- **proofshot CLI:** drives the real browser to prove the user-visible behavior is fixed.

If you are tempted to write the fix yourself "just to unblock" — stop and dispatch a heph2 lane. The discipline is the product.

## Step 0 — Collect inputs UPFRONT (before launching the workflow)

The Workflow runs in the background and **cannot** call `AskUserQuestion`. Gather everything first:

| Input | Why | If missing |
|---|---|---|
| `repo` (abs path) | where the bug lives | default to cwd only if unnamed |
| `issue` | the exact defect statement | ask |
| `ui_affecting` + `url` + `launch_cmd` | so proofshot can verify | operator value is **authoritative**; infer from repro only if you leave it unset |
| **login → `creds_file`** | write `LOGIN_URL`/`USERNAME`/`PASSWORD` to a `chmod 600` file OUTSIDE any repo; pass its path as `creds_file` (keeps the secret out of prompts/logs) | **ASK NOW** — the background run can't prompt, and a UI fix with no creds returns `status: BLOCKED` |
| **repo identity** → `repo_key` / `gotchas_path` / `remote` | so the Gotcha files to the RIGHT repo (worktree-safe) | the resolver derives it — see below |
| `test_cmd` (+ optional `typecheck_cmd`) | the fix lane's RED→GREEN and the post-merge re-run need the exact command | leave blank → heph2 detects the runner |
| env: `EXA_API_KEY` (`~/.config/exa/env.sh`) for exa; **heph2 reachable** — `codex` authenticates via GPTAuthWrapper2 (local proxy on `:4142`, tokens in `~/.codex/auth.json`); no Poe key needed | lanes need them | smoke-test before launch (below) |

Resolve the repo identity and write the creds file before launching:

```bash
# worktree-safe repo identity (origin-keyed; resolves to the SAME key from any worktree)
source /home/david/.claude/skills/triage2/references/repo-identity.sh
eval "$(triage_repo_identity "$REPO")"   # -> TRIAGE_REPO_KEY / TRIAGE_REPO_ROOT / TRIAGE_GOTCHAS / TRIAGE_REMOTE

# secret-safe creds (only if ui_affecting); never commit, never echo PASSWORD
umask 077; CF="${XDG_RUNTIME_DIR:-/tmp}/triage-creds-$$.env"
printf 'LOGIN_URL=%s\nUSERNAME=%s\nPASSWORD=%s\n' "$login_url" "$username" "$password" > "$CF"

# heph2 reachability smoke-test (proxy up + a 1-line run)
curl -sS -m4 -o /dev/null -w 'GPTAuthWrapper2: %{http_code}\n' http://127.0.0.1:4142/
HEPHAESTUS_MODEL=gpt-5.5 HEPHAESTUS_REASONING_EFFORT=high \
  hephaestus --file <(echo 'Reply READY and exit.') --dir /tmp --dangerous | tail -3
```

Use `AskUserQuestion` to collect the login. Pass `repo_key`, `gotchas_path` (=`$TRIAGE_GOTCHAS`), `remote`, and `creds_file` (=`$CF`) through the Workflow `args`; **delete `$CF` after the run**. Never put secrets in the repo or committed files.

**Allowlist the lane commands before launch (critical).** Workflow subagents run in `acceptEdits` and inherit your tool allowlist — but shell/MCP calls that are *not* allowlisted still prompt you mid-run, which stalls the "deterministic background run." The lanes shell out to these; add them to your allowlist (or run in a mode that permits them) first: `hephaestus`, `proofshot`, `agent-browser`, `git` (`worktree`/`merge`), and `python3 ~/.claude/skills/exa/scripts/exa_cli.py`. Also confirm the feature is on: Dynamic workflows are a research preview (Claude Code ≥ v2.1.154) — enable them in `/config` if the `Workflow` tool isn't available.

## The deterministic pipeline (the heart)

Run it with the `Workflow` tool. The full, runnable script is **[references/triage.workflow.js](references/triage.workflow.js)** — launch it with:

```
Workflow({ scriptPath: "/home/david/.claude/skills/triage2/references/triage.workflow.js",
           args: { repo, issue, lanes: 4, minConfidence: 0.7, maxRounds: 2,
                   ui_affecting, url, launch_cmd, test_cmd,
                   repo_key, gotchas_path, remote, creds_file } })
```

Phases (each `phase()` is its own progress group; `agent()` lanes are Claude subagents that dispatch heph2 via Bash):

1. **Characterize** — one lane reproduces the bug and captures the **literal** failing output, the user-visible surface, the launch command, the URL, and `ui_affecting`.
2. **Diagnose (fan-out, barrier)** — a planner proposes N **distinct, non-overlapping** root-cause hypotheses spanning different subsystems/failure modes. `parallel()` runs one heph2 lane per hypothesis. The barrier is correct here: synthesis must compare **all** lanes. Each lane returns `{hypothesis, evidence (file:line), confidence, proposed_fix, exa_used}`. **The script enforces the exa mandate**: a lane returning `confidence < 0.6` with `exa_used=false` is re-dispatched once, then excluded from synthesis.
3. **Synthesize** — pick the single root cause with the strongest **traced** evidence. If confidence `< minConfidence`, the script loops back to Diagnose with **fresh** hypotheses (loop-until-confident, capped at `maxRounds`); still short → returns `status: ESCALATE` for the operator.
4. **Fix** — one heph2 lane creates a git **worktree** + branch `triage/<slug>`, runs the **misfile guard** (`triage_assert_repo` → must resolve to `repo_key`, else `status: BLOCKED`), implements the fix **tests-first (RED→GREEN)** using `test_cmd`, and appends the Gotcha on that branch. Returns `{identity_ok, worktree_path, branch, head_sha, tests, test_stdout, gotcha_section}`.
5. **Verify** — `ui_affecting` is **operator-authoritative** (a lane may only *discover* it when you left it unset). If UI, a lane drives `proofshot` against the running app (sourcing `creds_file`); an independent skeptic lane tries to **refute** the fix. The script returns **`status: FIXED` only when** proofshot passed (or non-UI) **and** the skeptic confirmed **and** tests have literal GREEN stdout **and** the Gotcha landed **and** the identity guard held — otherwise **`status: NEEDS_REVIEW`** with the failing gate.

The orchestrator does Merge + Cleanup **after** the workflow returns `status: FIXED` (they need the active branch and user interaction). **By default the pipeline runs end-to-end with no mid-run review — the only human gates are merge and cleanup.**

### Workflow-feature notes (from the docs)

- **No mid-run user input.** A workflow can't prompt for anything except agent permission requests. That is why credentials are collected in Step 0, and why Merge + Cleanup live in the orchestrator. If you want a **human sign-off gate** between diagnosis and the fix, run them as **two separate workflows** (Characterize→Synthesize, then Fix→Verify) and review the first's return before launching the second.
- **Model.** Every workflow agent uses your session model (Opus). That is fine here: each lane is only a *dispatcher* — the heavy diagnostic/fix reasoning runs in **heph2 (gpt-5.5 high)** via the CLI, independent of the agent's own model.
- **Resume.** If a long heph2 run is interrupted, resume in the **same session** (`/workflows` → select → `p`, or relaunch with `resumeFromRunId`); completed lanes return cached results. Exiting Claude Code restarts the run fresh.
- **Save it.** After a clean run, `/workflows` → select → `s` saves the script as a reusable `/triage2-fix` command (`~/.claude/workflows/` for all projects).
- **Watch it.** `/workflows` shows phases, per-lane agent counts, tokens, and each lane's findings live.

## Verified tool invocations (use these exact surfaces)

**heph2** — every lane shells out to it; keep the env vars on the same command line:
```bash
HEPHAESTUS_MODEL=gpt-5.5 HEPHAESTUS_REASONING_EFFORT=high \
  hephaestus --file <brief.md> --dir <repo-or-worktree> --dangerous
# self-contained brief (codex has no memory of this chat); output lands in ~/.hephaestus/outputs/hephaestus-*.md
```

**exa** — heph2's mandated research lane when confidence is low (diagnosis mode = 5 Whys → root cause, verify, fix, prevention):
```bash
python3 ~/.claude/skills/exa/scripts/exa_cli.py run --query "<rewritten query>" --format compact-markdown
```

**proofshot** — prove the user-visible fix on the real app (NOT the `--launch/--scenarios` shape some skills imply — that is wrong):
```bash
proofshot start --description "verify <issue> fixed" --url <url> [--run "<launch_cmd>"]
proofshot exec open <login_url>
proofshot exec snapshot                         # discover field refs for the AI
proofshot exec fill <email-sel>    "<username>"
proofshot exec fill <password-sel> "<password>"
proofshot exec click <submit-sel>
proofshot exec find text "<post-login marker>" first   # confirm login
# …exercise the exact repro path, then screenshot the now-working surface…
proofshot exec screenshot proof-after.png
proofshot stop                                  # bundles proof artifacts
```
`proofshot exec` wraps `agent-browser` (`open/fill/click/find/snapshot/screenshot/get/is …`).

## Diagnostic fan-out rules

- **Diversify hypotheses.** Lane 1 may take the obvious guess; lanes 2..N must take *different* subsystems / failure modes. Non-obvious pathology is exactly why we fan out.
- **exa is mandatory at low confidence — and the script enforces it.** The brief tells heph2 to run exa below 0.6 (5-Whys, cite sources); the *script* then verifies `exa_used`: any lane with `confidence < 0.6 && exa_used=false` is **re-dispatched once with a hard exa instruction, then excluded** from synthesis. Not left to model goodwill.
- **Evidence or it didn't happen.** A hypothesis is only acceptable with `file:line` citations the synthesizer can re-open.
- **Loop, don't settle.** Below the confidence gate → another diagnostic round with fresh angles, capped, then escalate.

## Register the Gotcha (newest entry, repo's own format)

The Fix lane appends ONE entry to the resolved `gotchas_path` (`<repo-root>/Gotchas.md`) **before its commit** — after the misfile guard confirms the worktree resolves to `repo_key`, so it can never land in the wrong repo. Match the existing house format (see `/home/david/Projects/HyperVisa/Gotchas.md`):

```markdown
## §N — <one-line title of the trap>

**Discovered:** <YYYY-MM-DD>. **Severity:** <L1 LOW|L2 LIGHT|L3 MED|L4 HEAVY|L5 BLOCKING>. **Pin: no.**

### The misleading symptom
<what you saw first>

### The wrong conclusion
<the plausible-but-wrong read>

### The root cause
<the real cause, with file:line>

### The fix
<what changed, with the working contract / snippet>

### Verification
<the literal proofshot / test evidence that proves it>

### Sources
<exa citations, plan refs, commit SHA>
```

Severity ladder (same as the house ladder): **L1** trivial · **L2** one-line CLI/API mismatch · **L3** undocumented runtime behavior · **L4** non-obvious contradiction in core logic · **L5** changes an architectural fundamental (pause + notify operator). If `Gotchas.md` doesn't exist, create it with a short header before the first `## §1`.

## Repo identity & filing (so it can't misfile)

Two layers, both keyed to the repo being worked on:

- **Source of truth = in-repo** `<repo-root>/Gotchas.md`, committed with the fix so the finding travels with the code. The Fix lane writes it in the worktree (= repo root for that branch); it lands at the root on merge.
- **Host-level registry = `~/.triage/registry.json`** — the filing system that *recognises which repo* a run belongs to and points at its `Gotchas.md`. The orchestrator records each run after merge.

**Identity is worktree-safe and origin-keyed.** `references/repo-identity.sh` keys off the *common* git dir + `remote.origin.url` (normalized to `host/owner/repo`, abs-path fallback), so every worktree of a repo resolves to the SAME `repo_key`/root/Gotchas path — a linked worktree can't mint a phantom identity. `triage_assert_repo <path> <repo_key>` is the **misfile guard**: the Fix lane runs it before writing, and a mismatch returns `status: BLOCKED` instead of filing into the wrong repo. (Verified: from a linked worktree the resolver returns the identical key/root/Gotchas as the main checkout, and the guard refuses a mismatched key.)

## Merge to the active branch, then offer cleanup

Only when the workflow returned `status: FIXED` (script-verified) **and** you have re-verified the literal stdout yourself. If it returned `NEEDS_REVIEW` / `BLOCKED` / `ESCALATE`, **do not merge** — read `verify.*` + `gates`, correct, re-run.

```bash
ACTIVE=$(git -C "$REPO" rev-parse --abbrev-ref HEAD)     # merge target = the active branch
git -C "$REPO" merge --no-ff "$BRANCH"                   # $BRANCH = fix.branch; Gotchas.md merges with it
# re-run $test_cmd on ACTIVE; paste the literal result

# file the run in the host-level registry (in-repo Gotchas.md is already merged):
python3 /home/david/.claude/skills/triage2/references/file-gotcha.py record \
  --key "$TRIAGE_REPO_KEY" --root "$TRIAGE_REPO_ROOT" --gotchas "$TRIAGE_GOTCHAS" \
  --remote "$TRIAGE_REMOTE" --section "<§N>" --branch "$BRANCH" --sha "<head_sha>" --issue "$issue"

rm -f "$CF"                                              # delete the creds file
```

Then **ask** the user before removing anything:

```bash
git -C "$REPO" worktree remove <worktree_path>           # cleanup, only if the user says yes
git -C "$REPO" branch -d "$BRANCH"
```

Per the request: **all code must be merged to the active branch** at the end; worktree/branch cleanup is **optional and user-gated** — always ask "clean up the triage worktree and branch?" as the final step.

## Truth contract (overrides any urge to round up)

Declare the bug fixed **only** with literal evidence pasted inline:
- the proofshot run showing the previously-failing behavior now working (artifact path + the relevant stdout), AND
- the project's test command output on the active branch after merge.

A heph2 lane exiting `0` is necessary but **not** sufficient. Independently re-verify every subagent claim — a lane saying "done" means nothing until you re-open its cited `file:line` and re-run the gate. Forbidden without pasted stdout: "Verified: PASS", "tests passed", "I ran it and it worked".

## Red flags — STOP

| Thought | Reality |
|---|---|
| "Obvious cause, skip the fan-out" | Non-obvious pathology is *why* triage exists. Run ≥3 distinct lanes. |
| "I'll just patch it myself" | Orchestrator never writes the fix. Dispatch heph2. |
| "Confidence is fine, skip exa" | The *script* re-dispatches then drops a sub-0.6 lane with `exa_used=false`. You can't skip it. |
| "Tests pass, ship it" (no proofshot) | UI-affecting fixes need proofshot; `ui_affecting` is operator-authoritative so a lane can't silently downgrade it. |
| "Status is FIXED, just merge" | FIXED is script-gated on proofshot+skeptic+tests+gotcha+identity — but still re-verify the stdout. `NEEDS_REVIEW` → do not merge. |
| "File the Gotcha wherever" | The misfile guard files only to the resolved `repo_key`; a mismatch is `BLOCKED`. |
| "I'll ask for the login later" | The background workflow can't prompt. Write `creds_file` in Step 0 or a UI run is `BLOCKED`. |
| "Leave the worktree, it's fine" | Merge to the active branch, then ASK to clean up. |

## Related skills

- `hephaestus2` — the only authorized implementer (gpt-5.5 high)
- `exa` — mandated research lane at low confidence
- `Simplement` — sibling four-phase brownfield workflow (greenfield/slice builds)
- `checkit` / `peep` — contract-and-verify pairing for spec'd builds
- `superpowers:test-driven-development` — every heph2 fix brief carries a RED→GREEN step
- `superpowers:writing-skills` — applies to this skill's own evolution
