# IMPLEMENT THE FIX — tests-first (RED→GREEN), isolated worktree

You are a FRESH Codex session (gpt-5.5 high) with NO memory of any prior chat. Everything you need is
in this brief. You are implementing a single, already-diagnosed fix in an ISOLATED git worktree.
Be surgical and strictly typed. Touch only what the fix requires.

## Worktree (work HERE — already created off the repo HEAD on branch `triage/<slug>`)
`{{WT}}`

## The diagnosed root cause + precise fix to implement
SEVERITY: {{SEVERITY}}

FIX SPEC:
{{FIX_SPEC}}

## Reproduction this fix must resolve
{{REPRO}}

## Test command (run EXACTLY this for RED/GREEN; if blank, detect the repo's runner)
{{TEST_CMD}}

## Discipline (HARD)
1. **RED first.** Write a failing test that reproduces the defect at the right layer (backend
   pytest / FE jest / integration — whichever matches the bug). Run it via the Test command above;
   paste the literal RED stdout.
   - Backend python: activate the venv if needed (`source .venv/bin/activate`).
   - Frontend TS: also run the repo's typecheck script.
2. **GREEN.** Implement the minimal fix per the FIX SPEC. Re-run the SAME Test command; paste the
   literal GREEN stdout. Run the repo's typecheck/lint for the touched module and paste that too.
3. **Surgical.** Match existing style. Remove only orphans YOUR change creates. No drive-by refactors.
4. **Strictly typed.** Both Python and TypeScript must be strictly typed — no `any`, no untyped defs.

## Register the Gotcha BEFORE you commit
The orchestrating lane already ran the misfile guard — this worktree resolves to REPO_KEY
`{{REPO_KEY}}`, so `{{WT}}/Gotchas.md` IS the right repo's Gotchas file (it lands at the repo root on merge).
Append ONE new section to `{{WT}}/Gotchas.md` (create the file with a short header if absent),
matching the existing house format EXACTLY (dated `## §N — <title>`, then
**Discovered**/**Severity**/**Pin** line, then the sections: *The misleading symptom*,
*The wrong conclusion*, *The root cause* (with file:line), *The fix* (with the working snippet),
*Verification* (literal test/proofshot evidence), *Sources* (exa citations / commit SHA)).
Use the next free `§N`. Severity from the ladder: L1 trivial · L2 one-line CLI/API mismatch ·
L3 undocumented runtime behavior · L4 non-obvious contradiction in core logic · L5 architectural.

## Commit (on the worktree branch only — do NOT push, do NOT touch other branches)
`git add -A && git commit -m "fix(triage): <concise summary>"` after tests are GREEN and the Gotcha
is appended.

## Deliverable (return EXACTLY this structured object)
- `worktree_path`: `{{WT}}`
- `branch`: the `triage/<slug>` branch name
- `head_sha`: `git rev-parse HEAD` of your commit
- `files_changed`: array of paths you changed
- `tests`: exact test command(s) you ran
- `test_stdout`: the LITERAL passing (GREEN) stdout — never fabricate it
- `gotcha_appended`: true once the new `§N` section is in Gotchas.md
- `gotcha_section`: the exact `§N` label you appended (e.g. "§11")

Forbidden: reporting success without the literal GREEN stdout pasted into `test_stdout`.
