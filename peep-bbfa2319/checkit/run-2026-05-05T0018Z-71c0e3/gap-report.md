# Gap Report

## 1. Requirement satisfaction

- [PARTIAL] R1 — peep certificate flow self-archives after FORMAL CONCLUSION.
  Evidence: diff.txt:486-diff.txt:495 adds a router note, and diff.txt:527-diff.txt:608 / diff.txt:640-diff.txt:721 add SELF-ARCHIVE instructions to the Claude peep templates.
  If PARTIAL: the artifact writes are still placeholder comments (`# Write contract.md`, `# Write mental-model.brief.md`, `# Write mental-model.png`) at diff.txt:574-diff.txt:576 and diff.txt:687-diff.txt:689, and the diff shows no actual `~/peep-archive/` bootstrap artifact or committed archive state.

- [PARTIAL] R2 — `checkit` skill exists at `~/.claude/skills/checkit/SKILL.md` with progressive-disclosure structure and matching discovery patterns.
  Evidence: diff.txt:1-diff.txt:9 creates `claude/skills/checkit/SKILL.md` with name/description/triggers.
  If PARTIAL: the diff does not show the required `~/.claude/skills/checkit` symlink, the file is a 258-line monolithic workflow rather than the specified lean router + templates + references, and the referenced `references/verdict-ladder.md` / `references/blind-reconstruction-firewall.md` files are absent.

- [PARTIAL] R3 — checkit reads archived inputs and the actual project diff.
  Evidence: diff.txt:51-diff.txt:60 lists archived inputs and diff.txt:104-diff.txt:110 computes a diff from manifest repo/base/head.
  If PARTIAL: `spec.txt` is missing from the input table and the adversarial brief input list (diff.txt:280-diff.txt:293), despite R3 requiring checkit to read `spec.txt` from `~/peep-archive/<peepID>/`.

- [NOT_SATISFIED] R4 — checkit performs blind forensic reconstruction producing `actual-architecture.brief.md` and `actual-architecture.png` without mental-model context.
  Evidence: diff.txt:23-diff.txt:26 explicitly says this is not blind verification, and diff.txt:242-diff.txt:250 says true blind reconstruction is future hardening/out of scope.

- [PARTIAL] R5 — checkit performs gap analysis comparing actual-architecture artifacts against peep mental-model artifacts and emits `gap-report.md` citing invariants or anti-claims.
  Evidence: diff.txt:116-diff.txt:135 dispatches adversarial gap analysis, and diff.txt:312-diff.txt:343 requires invariant and anti-claim sections in `gap-report.md`.
  If PARTIAL: no diff hunk creates the required `actual-architecture.brief.md` / `actual-architecture.png`, and no hunk compares those artifacts against `mental-model.brief.md` / `mental-model.png`; the shipped flow audits contract + diff directly instead.

- [PARTIAL] R6 — checkit invokes `/proofshot` for UI features or behavioral ambiguity.
  Evidence: diff.txt:137-diff.txt:171 documents a UI-affecting proofshot branch and diff.txt:164-diff.txt:168 lists proofshot arguments.
  If PARTIAL: the only trigger is `UI_BEHAVIOR_AFFECTING=yes`, not “CHANGE SURFACE includes any frontend file” or “gap-report flags behavioral ambiguity”; the proofshot invocation itself is only a placeholder comment at diff.txt:155-diff.txt:159, not an actual command.

- [NOT_SATISFIED] R7 — `verdict.md` contains exactly one six-rung verdict token: PERFECT, VERIFIED, ARCH_GAP, LOGIC_GAP, BEHAVIORAL_FAIL, FAILED.
  Evidence: diff.txt:38-diff.txt:49 defines four different tokens (`MANIFEST_INCOMPLETE`, `BEHAVIORAL_FAIL`, `GAP`, `PASS`), and diff.txt:173-diff.txt:180 applies that incompatible four-token ladder.

- [PARTIAL] R8 — when verdict is LOGIC_GAP, BEHAVIORAL_FAIL, or FAILED, checkit writes `corrective-prompt.md`.
  Evidence: diff.txt:187-diff.txt:197 writes `corrective-prompt.md` for any non-`PASS` verdict.
  If PARTIAL: the shipped verdict set lacks `LOGIC_GAP` and `FAILED` entirely (diff.txt:38-diff.txt:49), so the required branches cannot be represented.

- [SATISFIED] R9 — checkit commits and pushes the run folder to the orphan branch immediately.
  Evidence: diff.txt:199-diff.txt:208 adds the run-folder `git add`, `git commit`, `git pull --rebase`, and `git push` sequence.

- [NOT_SATISFIED] R10 — invocation surface is `/checkit [<peepID>]`, with no-arg fallback to the most recent peep folder by mtime.
  Evidence: diff.txt:28-diff.txt:36 makes `<peepID>` mandatory and explicitly says “No mtime fallback, no auto-detect.”

## 2. Invariant preservation

- [PRESERVED] INV1 — peep certificate output remains the primary artifact.
  Evidence: diff.txt:527-diff.txt:529 appends SELF-ARCHIVE after FORMAL CONCLUSION and MENTAL MODEL DIAGRAM, so the certificate body is not replaced.

- [VIOLATED] INV2 — checkit MUST do blind reconstruction.
  Evidence: diff.txt:23-diff.txt:26 explicitly rejects blind verification, and diff.txt:242-diff.txt:250 defers true blind reconstruction to future hardening.

- [VIOLATED] INV3 — harness symlink pattern keeps canonical source in one place.
  Evidence: diff.txt:726-diff.txt:731 adds a Codex-side `checkit` copy, while no diff hunk creates the required `~/.claude/skills/checkit` symlink; this duplicates source instead of preserving a single canonical location.

- [PRESERVED] INV4 — imagegen delegates through hephaestus, not direct OpenAI API.
  Evidence: diff.txt:523-diff.txt:525 keeps image rendering routed through the `imagegen` skill and no diff hunk introduces direct OpenAI API calls.

- [PRESERVED] INV5 — peepID idempotency.
  Evidence: diff.txt:531-diff.txt:537 and diff.txt:644-diff.txt:650 compute `peepID` from `sha256` of the byte-exact SPEC and state same SPEC -> same archive folder.

- [VIOLATED] INV6 — proofshot session lifecycle is start → drive → stop → bundle.
  Evidence: diff.txt:155-diff.txt:159 only contains comments to invoke proofshot and save artifacts; there is no start/drive/stop/bundle lifecycle encoded in the diff.

## 3. Scope creep

- `claude/skills/checkit/templates/adversarial-audit.md` (+122, -0) — adds an adversarial audit template under a different name than the contract’s listed `templates/forensic-audit.md`.
  Note: not in CHANGE SURFACE; flag for human review.

- `claude/skills/firecrawl/scripts/firecrawl_cli.py` (+62, -7) — changes Firecrawl API-key loading by adding env-file parsing fallback.
  Note: not in CHANGE SURFACE; flag for human review.

- `codex/skills/checkit/SKILL.md` (+258, -0) — adds a Codex-side `checkit` skill mirror.
  Note: not in CHANGE SURFACE; flag for human review.

- `codex/skills/checkit/templates/adversarial-audit.md` (+122, -0) — adds a Codex-side adversarial audit template.
  Note: not in CHANGE SURFACE; flag for human review.

- `codex/skills/firecrawl/scripts/firecrawl_cli.py` (+62, -7) — mirrors the unrelated Firecrawl API-key loading change on the Codex side.
  Note: not in CHANGE SURFACE; flag for human review.

## 4. Anti-claims

- VIOLATED: “checkit itself is NOT mirrored to codex.” — Evidence: diff.txt:726-diff.txt:731 creates `codex/skills/checkit/SKILL.md`.

- VIOLATED: “No `~/.codex/skills/checkit/` mirror. checkit is Claude-only this round per user decision. Do NOT draw a Codex-side mirror.” — Evidence: diff.txt:726-diff.txt:731 and diff.txt:990-diff.txt:995 add Codex-side `checkit` files.

- VIOLATED: “No checkit access to mental-model.png in phase 1.” — Evidence: diff.txt:23-diff.txt:26 says the implementation is not blind, and diff.txt:59-diff.txt:60 lists `mental-model.brief.md` / `mental-model.png` as adversarial-agent context rather than sealing them until a phase-2 comparison.

## 5. Test obligations

- [MISSING] NT1 — run peep on a small SPEC and verify archive files plus orphan-branch log.
  If PRESENT: no test file or test command hunk in diff; `build-manifest.json` also lists an empty `tests` array.

- [MISSING] NT2 — run `/checkit <peepID>` on a known folder and verify blind reconstruction output isolation.
  If PRESENT: no test file or test command hunk in diff; the shipped design explicitly says blind reconstruction is not implemented at diff.txt:23-diff.txt:26.

- [MISSING] NT3 — verify `gap-report.md` cites an INV identifier or anti-claim phrase.
  If PRESENT: no test file or test command hunk in diff; only the audit template asks future reviewers to do this (diff.txt:312-diff.txt:343).

- [MISSING] NT4 — verify `verdict.md` contains one of the six required verdict tokens.
  If PRESENT: no test file or test command hunk in diff; the implementation uses a different four-token verdict set at diff.txt:38-diff.txt:49.

- [MISSING] NT5 — verify archive git log advances by one per checkit run and remote `peep` matches local HEAD.
  If PRESENT: no test file or test command hunk in diff; only an untested commit/push recipe exists at diff.txt:199-diff.txt:208.

- [MISSING] NT6 — with two peep folders, `/checkit` without an arg targets the most recent mtime.
  If PRESENT: no test file or test command hunk in diff; the shipped invocation rejects the no-arg behavior at diff.txt:34-diff.txt:36.

## 6. Summary

The shipped diff adds a `checkit` skill and peep self-archive instructions, but it deliberately drops the contract’s blind-reconstruction architecture and six-rung verdict ladder. Several requirements are only instruction-level placeholders, especially archive artifact writes and proofshot execution, while every new test obligation is missing from the diff. There is clear scope creep: unrelated Firecrawl auth changes and a Codex-side `checkit` mirror that the contract and mental model explicitly forbid. Overall confidence in these findings is high because the gaps are visible in the diff itself, including direct contradictions such as “not blind” and “No mtime fallback.”

GAP_FINDINGS_FOUND
