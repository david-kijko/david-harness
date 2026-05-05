# Corrective prompt for next builder session — peep-bbfa2319 / GAP

The checkit verdict is GAP. The shipped diff (069418f..e775a59) implements
the checkit feature but has been judged against the v2.2 contract.md, which
predates user-approved simplifications. Several gaps are real bugs; others
reflect spec drift the user explicitly asked for. Triage below.

## Real ship-blockers (must fix in code)

1. **Peep SELF-ARCHIVE template has placeholder comments, not executable
   write logic.** R1 is PARTIAL because brownfield/greenfield SELF-ARCHIVE
   sections at diff.txt:574-576 and diff.txt:687-689 contain `# Write
   contract.md`, `# Write mental-model.brief.md`, `# Write mental-model.png`
   as comments. An agent following the template will not know how to
   actually write these files (the certificate body is in their context;
   they must extract it). Fix: either replace the comments with explicit
   instructions ("the agent writes the certificate code-block above to
   contract.md, the mental-model section to mental-model.brief.md, and
   the rendered image to mental-model.png") OR provide a helper script.

2. **proofshot invocation is placeholder comments.** R6/INV6 PARTIAL/
   VIOLATED because checkit/SKILL.md:155-159 only describes the proofshot
   call in prose, never executes it. Fix: write a concrete invocation
   pattern (likely a shell command calling /proofshot with the manifest
   fields).

3. **`spec.txt` missing from checkit input table.** R3 PARTIAL because
   while spec.txt IS archived by peep, checkit/SKILL.md doesn't list it
   as an input the adversarial reviewer reads. Add it to the input table
   and to adversarial-audit.md template.

## Spec-drift findings (contract is stale, NOT real bugs)

These findings reflect user-approved simplifications applied AFTER the
contract was archived. Resolution: rewrite contract.md as contract-v2.md
(or amend in place) to match the user's clarified intent.

4. **Verdict ladder collapsed from 6 rungs to 4.** R7 NOT_SATISFIED.
   User approved dropping {PERFECT, VERIFIED, ARCH_GAP, LOGIC_GAP} into
   a single {PASS, GAP} pair, with BEHAVIORAL_FAIL and MANIFEST_INCOMPLETE
   distinct. Update contract R7 to declare the 4-token ladder.

5. **Blind reconstruction dropped.** R4 NOT_SATISFIED, INV2 VIOLATED.
   User approved dropping the sealed temp dir / phase-1/phase-2 / blind
   reconstruction architecture because it was policy-not-enforcement
   theater on this machine. Update contract R4 + INV2 to remove the
   blind-reconstruction requirement and document the bias-mitigation as
   "adversarial framing of one agent" instead.

6. **mtime fallback dropped.** R10 NOT_SATISFIED. User approved making
   peepID mandatory ("no mtime fallback, no auto-detect"). Update contract
   R10 to require explicit peepID arg.

7. **checkit IS mirrored to codex.** INV3 + anti-claim VIOLATED. User
   later said "implement please for both codex and .claude", reversing
   the earlier "Claude-only" decision. Update contract INV3 + anti-claim
   list to permit the codex mirror.

8. **References dir not created.** R2 PARTIAL — contract listed
   `references/verdict-ladder.md` and `references/blind-reconstruction-
   firewall.md`. With user-approved simplifications, the verdict ladder
   is short enough to live inline in SKILL.md (1 inline section), and
   blind-reconstruction-firewall is moot (dropped). Update contract to
   remove these references.

## Actually-out-of-scope creep (legitimately not the contract's job)

9. **Firecrawl env-fallback in the diff (069418f..4fe6e18 portion).**
   Unrelated commit included in the audited diff range because checkit
   was implemented across multiple commits. Fix: re-run checkit with a
   tighter range (e.g. base=4fe6e18 head=e775a59) so only the checkit
   work is audited.

## Test obligations (NT1-NT6) all MISSING — real

The contract specified six runnable tests; none were written. This
checkit run IS NT1+NT2+NT5 partially (a real /checkit invocation that
produced a verdict, with the run folder committed). NT3, NT4, NT6
remain unwritten. Add as real tests OR document as informal manual
verification.

## Recommended next action

Update contract.md → contract-v2.md applying findings 4-8, then re-run
/checkit with a tighter base..head range. Real ship-blockers 1-3 fix in
code first.
