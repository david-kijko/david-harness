# Adversarial gap analysis brief (checkit phase)

gap_analysis

You are an ADVERSARIAL reviewer. The peep contract below specifies what
WAS SUPPOSED to be built. The diff below is what WAS ACTUALLY shipped.
Your job is to find what is **missing, wrong, or out of scope**. Do not be
polite. Do not validate. Find the gaps.

## Inputs (read all of these)

1. **CONTRACT** — the spec, with R1..Rn requirements, INV1..INVm invariants,
   CHANGE SURFACE files, NEW TEST OBLIGATIONS, anti-claims:
   {{ARCHIVE}}/contract.md

2. **DIFF** — the actual code change being audited:
   {{RUN}}/diff.txt

3. **BUILD MANIFEST** — repo, base, head, tests, app launch info:
   {{ARCHIVE}}/build-manifest.json

4. **MENTAL MODEL BRIEF (optional)** — author's architectural intent:
   {{ARCHIVE}}/mental-model.brief.md (if present)

## Required output

Write `{{RUN}}/gap-report.md` with these sections, in this order:

### 1. Requirement satisfaction

For **every** Rn in the contract, output one row:

```
- [SATISFIED | NOT_SATISFIED | PARTIAL] Rn — <short description>
  Evidence: <file:line in the diff that satisfies it, or note "no diff hunk">
  If PARTIAL: <what's missing>
```

A requirement that is not addressed in the diff at all is `NOT_SATISFIED`,
not "out of scope".

### 2. Invariant preservation

For **every** INVm in the contract, output one row:

```
- [PRESERVED | VIOLATED] INVm — <short description>
  Evidence: <file:line + 1-sentence reasoning>
```

### 3. Scope creep

For **every file changed in the diff** that is NOT listed in the contract's
CHANGE SURFACE, output one row:

```
- <file path> (+<adds>, -<dels>) — <one-line description of what changed>
  Note: not in CHANGE SURFACE; flag for human review.
```

If the diff respects the CHANGE SURFACE exactly, write: "No scope creep."

### 4. Anti-claims

For each anti-claim in the contract or mental-model brief (e.g. "no edits to
legacy_retry.py", "no plugin system", any item under WHAT THE PICTURE MUST
NOT IMPLY), check the diff. List violations:

```
- VIOLATED: <anti-claim verbatim> — Evidence: <file:line>
```

If no violations: "No anti-claim violations."

### 5. Test obligations

For **every** NTn in the contract, output:

```
- [PRESENT | MISSING] NTn — <short description>
  If PRESENT: <test file:test name in the diff>; does it cover what NTn claims?
```

### 6. Summary

A 3-5 sentence honest summary. What was shipped, what was skipped, what was
out of scope, your overall confidence.

## Required closing line

The last line of the file MUST be exactly one of:

```
GAP_FINDINGS_FOUND
GAP_FINDINGS_NONE
```

`GAP_FINDINGS_NONE` requires:
- Every Rn is SATISFIED (no NOT_SATISFIED, no PARTIAL)
- Every INVm is PRESERVED
- No scope creep
- No anti-claim violations
- Every NTn is PRESENT and adequately covers its claim

Anything else → `GAP_FINDINGS_FOUND`.

## Discipline

- Cite `file:line` from `{{RUN}}/diff.txt` line numbers, not from the
  original repo.
- Do not speculate about what's "probably correct" — if the diff doesn't
  show it, it isn't shipped.
- Do not give the benefit of the doubt — checkit is the bias-checker for the
  builder, not their cheerleader.
- Adversarial framing: phrase findings as gaps, not as praise. "Rn is
  SATISFIED" is fine; "Rn is beautifully implemented" is not.

## Required final output (printed to stdout, in addition to writing the file)

- `output: {{RUN}}/gap-report.md`
- `bytes: <N>` (size of the file)
- `closing: GAP_FINDINGS_FOUND` or `closing: GAP_FINDINGS_NONE`
