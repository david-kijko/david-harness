# SEMI-FORMAL BROWNFIELD CONSTRUCTION CERTIFICATE — peep-bbfa2319

Template: `peep/templates/brownfield-construction.md` (this is an addition to an
existing project: the david-harness skill repo).

## DEFINITIONS

- D1 SUFFICIENT iff every Rn has at least one mapped CHANGE SURFACE row AND at least one NTn.
- D2 MINIMAL iff every CHANGE SURFACE row cites at least one Rn.
- D3 COMPATIBLE iff every existing caller is preserved or its breakage is justified.
- D4 VERIFIABLE iff every Rn maps to at least one NTn whose pass/fail is observable.

## SPEC (verbatim — see spec.txt for the byte-exact source the peepID hashes)

The user requested a verifier skill `checkit` that:

1. closes the loop on peep contracts by forensically auditing what the builder
   actually shipped against what the contract specified;
2. is orchestrated with peep so each contract is assigned a deterministic
   `peepID = first 8 hex chars of sha256(verbatim SPEC)` and archived to a backup
   folder on an orphan branch `peep` of the david-harness GitHub repo;
3. corresponding checkit verification artifacts live in the same archive with
   local git versioning (multiple `run-N/` subdirectories per peepID);
4. is implemented as a Claude skill at `~/.claude/skills/checkit/SKILL.md`,
   version-controlled through the harness repo, delegating heavy work
   (image generation, multi-file diff analysis, browser tests) to hephaestus;
5. uses the existing imagegen skill for image rendering;
6. pushes the orphan branch immediately after each peep contract and after each
   checkit verification run.

The forensic-feature-verifier sub-spec (verbatim from the user) defines checkit's
internal workflow: blind reconstruction first, gap analysis second, behavioral
validation via proofshot third, contract cross-reference fourth, verdict from a
six-rung confidence ladder (PERFECT, VERIFIED, ARCH_GAP, LOGIC_GAP,
BEHAVIORAL_FAIL, FAILED), with a corrective-prompt.md emitted on the failing
verdicts.

## SPEC DECOMPOSITION (atomic, testable)

- R1: peep certificate flow self-archives. After the FORMAL CONCLUSION step, the
  agent computes peepID, creates `~/peep-archive/<peepID>/`, writes spec.txt,
  contract.md, mental-model.brief.md, mental-model.png, commits, and pushes the
  orphan branch.
- R2: skill `checkit` exists at `~/.claude/skills/checkit/SKILL.md` with progressive-
  disclosure structure (lean router + templates + references), name and
  description matching the discovery patterns the user invokes (`/checkit`,
  "verify the build", "audit the diff", "checkit", etc).
- R3: checkit reads its inputs from `~/peep-archive/<peepID>/` —
  contract.md, spec.txt, mental-model.brief.md, mental-model.png — and the actual
  code diff from the project repo the builder modified.
- R4: checkit performs *blind* forensic reconstruction. The subagent that
  produces `actual-architecture.brief.md` and `actual-architecture.png` MUST
  NOT have `mental-model.png` or `mental-model.brief.md` in its prompt context.
  Enforced by dispatching a fresh hephaestus call with only diff + contract +
  spec.
- R5: checkit performs gap analysis comparing the actual-architecture artifacts
  against the peep mental-model artifacts, emitting `gap-report.md` that cites
  at least one specific INVARIANT or anti-claim from the peep brief.
- R6: checkit invokes `/proofshot` for UI features (when the contract's CHANGE
  SURFACE includes any frontend file or when the gap-report flags behavioral
  ambiguity).
- R7: checkit emits `verdict.md` containing exactly one of:
  PERFECT, VERIFIED, ARCH_GAP, LOGIC_GAP, BEHAVIORAL_FAIL, FAILED.
- R8: when verdict ∈ {LOGIC_GAP, BEHAVIORAL_FAIL, FAILED}, checkit additionally
  writes `corrective-prompt.md` — a structured prompt the builder agent reads
  on next dispatch.
- R9: checkit commits and pushes the run folder to the orphan branch immediately.
- R10: invocation surface is `/checkit [<peepID>]`. Without arg → most recent
  peep folder by mtime. With arg → that specific contract.

## EXISTING PATTERN SURVEY (guards B1, B2)

| Concern | Hypothesis | Evidence | Decision |
|---|---|---|---|
| Skill structure / progressive disclosure | exists | `peep/SKILL.md` (60 lines) + `templates/` + `references/` (line 23 of peep/SKILL.md routes to templates) | REUSE |
| Image generation | exists | `imagegen/SKILL.md` (single file, delegates to hephaestus → Codex `$imagegen`) | REUSE — checkit calls `/imagegen` the same way peep's MENTAL MODEL DIAGRAM step does |
| Hephaestus delegation pattern | exists | `hephaestus` skill, `hephaestus --file <brief>` accepts brief files | REUSE |
| Browser/UI verification | exists | `proofshot` skill listed in available-skills | REUSE — checkit invokes `/proofshot` for UI features |
| Orphan branch worktree | none in repo | `git branch -a` showed only `main` before this turn | NEW (created this turn at `~/peep-archive`) |
| Skill install pattern (symlink to harness) | exists | `~/.claude/skills/peep -> ~/david-harness/claude/skills/peep` (this turn) + `setup/install-claude.sh` loops over `claude/skills/*` | REUSE |
| peepID generation | none | new concept | NEW — sha8(SPEC) per this design |
| Verdict ladder | none | new concept | NEW — six-rung ladder per user's sub-spec |
| Multi-skill bundle convention | exists | the harness uses `claude/skills/<name>/` parallel to `codex/skills/<name>/` for cross-runtime skills, but firecrawl + peep are mirrored. checkit is Claude-only per user decision. | DEVIATE intentionally — only `claude/skills/checkit/` is created |

## INTEGRATION POINTS

- IP1: `peep/templates/brownfield-construction.md` — append a SELF-ARCHIVE section
  after FORMAL CONCLUSION that computes peepID and writes the archive folder.
- IP2: `peep/templates/greenfield-construction.md` — same append.
- IP3: `peep/SKILL.md` — note the v2.3 self-archive behaviour in the router intro.
- IP4: `~/peep-archive/` worktree (already created this turn, branch `peep`).
- IP5: new `~/david-harness/claude/skills/checkit/` subtree.
- IP6: new symlink `~/.claude/skills/checkit -> ~/david-harness/claude/skills/checkit`
  (auto-installed by `setup/install-claude.sh` on next run; manual on first
  install).

## INVARIANTS THAT MUST BE PRESERVED (guards B3)

- INV1: peep certificate output remains the primary artifact.
  Evidence: `peep/templates/brownfield-construction.md:25-128` — the certificate
  is a code block the agent fills inline.
  Why preserved: archive step is APPENDED after FORMAL CONCLUSION, never
  replaces or modifies the certificate body.

- INV2: checkit MUST do blind reconstruction.
  Evidence: user's verbatim sub-spec ("CRITICAL: Do NOT look at the 'PEEP
  Architecture PNG' during this step").
  Why preserved: enforcement is structural — checkit dispatches reconstruction
  in a fresh hephaestus call whose prompt contains only the diff + contract +
  spec; the brief explicitly forbids reading `mental-model.png`. The comparison
  phase is a separate, second hephaestus dispatch that receives both images.

- INV3: harness symlink pattern (canonical source in one place).
  Evidence: prior turn's relink work; `setup/install-claude.sh` lines 18-39.
  Why preserved: checkit is created at the harness path first, then symlinked.

- INV4: imagegen delegates through hephaestus, not direct OpenAI API.
  Evidence: `imagegen/SKILL.md` mandates this and lists it as a hard rule.
  Why preserved: checkit's image step invokes `/imagegen` like peep does.

- INV5: idempotency of peepID.
  Evidence: `peepID = sha8(verbatim SPEC)` is deterministic.
  Why preserved: filenames inside the folder are fixed (`spec.txt`, `contract.md`,
  `mental-model.{brief.md,png}`); only `checkit/run-N/` advances per run.
  Re-running peep on the same SPEC writes into the same folder (overwriting
  contract+brief+png is acceptable as the artifacts are derived from SPEC).

- INV6: proofshot session lifecycle (start → drive → stop → bundle).
  Evidence: proofshot skill description.
  Why preserved: checkit's UI verification phase opens a session, runs through
  the contract's NEW TEST OBLIGATIONS for UI flows, then stops and saves the
  bundle to `checkit/run-N/proofshot/`.

## CHANGE SURFACE (guards B4 via D2)

| File | New / Modified | Approx lines | Discharges Rn |
|---|---|---|---|
| `claude/skills/peep/templates/brownfield-construction.md` | Modified | +30 | R1 |
| `claude/skills/peep/templates/greenfield-construction.md` | Modified | +30 | R1 |
| `claude/skills/peep/SKILL.md` | Modified | +6 | R1 |
| `claude/skills/checkit/SKILL.md` | New | ~140 | R2, R3, R10 |
| `claude/skills/checkit/templates/forensic-audit.md` | New | ~120 | R3, R4, R5, R6, R7, R8, R9 |
| `claude/skills/checkit/references/verdict-ladder.md` | New | ~70 | R7, R8 |
| `claude/skills/checkit/references/blind-reconstruction-firewall.md` | New | ~50 | R4 (the structural enforcement of INV2) |
| `~/.claude/skills/checkit` (symlink) | New | 1 | R2 (install) |
| `~/peep-archive/` | Bootstrapped this turn | n/a | infrastructure for R1, R9 |

Mirror in `codex/skills/peep/...` is needed for the peep template edits because
peep is mirrored to codex. checkit itself is NOT mirrored to codex.

## REQUIREMENT → CODE MAPPING (guards B5 via D1)

- R1 → templates/brownfield-construction.md (+30 lines), greenfield-construction.md (+30), SKILL.md (+6). Inference type: invariant-preservation.
- R2 → checkit/SKILL.md. Inference type: pattern-reuse (peep's progressive-disclosure layout).
- R3 → checkit/SKILL.md "Locate inputs" step + checkit/templates/forensic-audit.md.
- R4 → checkit/templates/forensic-audit.md two-phase dispatch + references/blind-reconstruction-firewall.md. Inference type: new-construction.
- R5 → templates/forensic-audit.md gap-analysis step.
- R6 → templates/forensic-audit.md proofshot conditional step.
- R7 → templates/forensic-audit.md verdict step + references/verdict-ladder.md.
- R8 → templates/forensic-audit.md corrective-prompt branch + references/verdict-ladder.md.
- R9 → templates/forensic-audit.md closing step.
- R10 → checkit/SKILL.md frontmatter description + locate-by-mtime fallback.

## BACKWARD-COMPATIBILITY TRACE (guards B6, B7 via D3)

Existing callers of peep templates: agents that invoke peep on a coding task.
- C1: any agent currently using peep/templates/brownfield-construction.md.
  After change: certificate body is unchanged through FORMAL CONCLUSION;
  self-archive section is appended. STILL SATISFIED.
- C2: any agent using greenfield template. Same. STILL SATISFIED.

Existing tests touching the change surface (PASS_TO_PASS):
- T1: `peep/benchmarks/` — A/B comparisons of peep outputs vs baseline. They
  capture certificate prose, not archive behavior. STILL PASSES.
- T2: setup/install-claude.sh — loops over `claude/skills/*/` and creates
  symlinks. checkit/ is just one more directory. STILL PASSES (no script
  change needed).

## NEW TEST OBLIGATIONS (guards D4)

- NT1 (R1): run peep on a small SPEC. Verify
  `~/peep-archive/peep-<sha8>/{spec.txt,contract.md,mental-model.brief.md,mental-model.png}`
  all exist and `git -C ~/peep-archive log --oneline | head -2` shows the
  contract commit followed by the init commit.
  Runnable: `ls ~/peep-archive/peep-<sha8>/ && git -C ~/peep-archive log --oneline | head -2`.

- NT2 (R3, R4): given a known peep folder, run `/checkit <peepID>` on a small
  builder diff. Verify checkit/run-1/actual-architecture.brief.md exists and
  contains no string from mental-model.brief.md (proof of blind reconstruction
  by output isolation).
  Runnable: `comm -12 <(sort ~/peep-archive/<id>/mental-model.brief.md) <(sort ~/peep-archive/<id>/checkit/run-1/actual-architecture.brief.md) | wc -l` should be near zero (some incidental overlap of common English words is acceptable; *substantive sentences* matching is the failure).

- NT3 (R5): verify checkit/run-1/gap-report.md cites at least one INVARIANT
  identifier ("INV1", "INV2", …) or anti-claim phrase from mental-model.brief.md.
  Runnable: `grep -E "INV[0-9]+|anti-claim|MUST NOT" ~/peep-archive/<id>/checkit/run-1/gap-report.md`.

- NT4 (R7): verdict.md contains one of the six tokens.
  Runnable: `grep -E "^(PERFECT|VERIFIED|ARCH_GAP|LOGIC_GAP|BEHAVIORAL_FAIL|FAILED)$" ~/peep-archive/<id>/checkit/run-1/verdict.md`.

- NT5 (R9): `git -C ~/peep-archive log --oneline | wc -l` advances by 1 per run; `git ls-remote origin peep | head -1` matches the local HEAD SHA.

- NT6 (R10): with two peep folders present, `/checkit` (no arg) targets the
  one with the most recent mtime.

## COUNTEREXAMPLE / SUFFICIENCY CHECK

- R1: Property = "after peep certificate completion, archive folder exists and
  is pushed." Soundness sketch: the SELF-ARCHIVE section is a non-optional
  step inside the certificate template, parallel to FORMAL CONCLUSION. An
  agent that skips it produces an incomplete certificate (the same way
  skipping CHANGE SURFACE would). Counterexample considered: network failure
  on push. Mitigation: archive is local-committed first; sync command exists
  for retry; the agent reports "archived locally, push pending: <error>".

- R4: BLIND RECONSTRUCTION is the trickiest invariant. Soundness sketch: the
  reconstruction subagent's prompt contains only `{diff, contract.md, spec.txt}`
  — no `mental-model.png`, no `mental-model.brief.md`. Hephaestus has no way to
  see them unless the brief mentions their paths. Counterexample considered:
  an agent that reads the contract.md and notices "mental-model.png exists at
  X" and then opens it. Mitigation: the brief explicitly forbids reading
  anything in the peep-archive folder *other than* spec.txt and contract.md;
  the second-phase comparison subagent is the only one allowed to load
  mental-model.png.

- R7: enumerated finite ladder; sound by exhaustion.

- R8: corrective-prompt is generated only on three branches; each branch has
  template content in `references/verdict-ladder.md`.

## FORMAL CONCLUSION

- D1 SUFFICIENT: YES — every R1-R10 has a CHANGE SURFACE row AND an NTn.
- D2 MINIMAL: YES — every CHANGE SURFACE row cites at least one Rn.
- D3 COMPATIBLE: YES — peep certificate flow preserved, no test regression.
- D4 VERIFIABLE: YES — every Rn has a runnable NTn.

**Plan is READY TO IMPLEMENT: YES.**

## SELF-ARCHIVE (this is the v2.3 step being prototyped here, applied to itself)

- peepID: `peep-bbfa2319`
- Archive: `/home/david/peep-archive/peep-bbfa2319/`
- Files: spec.txt, contract.md, mental-model.brief.md, mental-model.png
- Branch: `peep` in `david-harness` (orphan)
- Commit: pending after this file + brief + png are written
- Push: pending after commit
