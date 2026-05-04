# Template: Patch Equivalence Verification

**Use when**: comparing two patches/diffs, checking if a generated patch matches a reference, verifying that two changes produce the same observable behavior.

**Failure modes this template guards against** (full catalog in `references/failure-modes.md`):
- Incomplete execution tracing (assumes function behavior; doesn't read the source)
- Third-party library semantics (guesses from name)
- Dismissing subtle differences (notices a difference, says "doesn't matter")

If you need to *explore* the codebase before you can fill the certificate, use the loop in `references/exploration-loop.md`. If you need to tag claims by inference type, see `references/claim-types.md`.

---

## Fill the certificate. Every bracketed field. Read the source.

```
SEMI-FORMAL PROOF OF PATCH EQUIVALENCE

DEFINITIONS
D1: Two patches are EQUIVALENT MODULO TESTS iff executing the existing
    repository test suite (FAIL_TO_PASS ∪ PASS_TO_PASS) produces
    identical pass/fail outcomes for both patches.
D2: The relevant tests are ONLY those in FAIL_TO_PASS and PASS_TO_PASS
    (the existing suite). Hypothetical tests do not count.

PREMISES (state what each patch ACTUALLY does — read the diff)
P1: Patch 1 modifies [file(s)] by [specific change description with line context]
P2: Patch 2 modifies [file(s)] by [specific change description with line context]
P3: The FAIL_TO_PASS test(s) [name(s)] check [specific behavior — quote the assertion]
P4: The PASS_TO_PASS test(s) that touch the change surface check [behavior]

ANALYSIS OF TEST BEHAVIOR

For each FAIL_TO_PASS test:
  Claim 1.1: With Patch 1, test [name] will [PASS/FAIL]
             because [trace through the code from test entry to assertion,
                      with file:line citations at each hop]
  Claim 1.2: With Patch 2, test [name] will [PASS/FAIL]
             because [trace]
  Comparison: [SAME/DIFFERENT] outcome

For each PASS_TO_PASS test that COULD be affected differently by the two patches:
  Claim 2.1: With Patch 1, behavior is [description]
  Claim 2.2: With Patch 2, behavior is [description]
  Comparison: [SAME/DIFFERENT]

EDGE CASES THE EXISTING TESTS EXERCISE
(Only analyze edges the actual tests reach. Hypothetical edges = scope creep.)

E1: [Edge case the test exercises]
  - Patch 1 behavior: [specific output]
  - Patch 2 behavior: [specific output]
  - Test outcome same: [YES/NO]

COUNTEREXAMPLE  (REQUIRED if claiming NOT EQUIVALENT)
Test [name] PASSES with Patch 1 because [reason with file:line]
Test [name] FAILS with Patch 2 because [reason with file:line]
Therefore patches produce DIFFERENT test outcomes.

— OR —

NO COUNTEREXAMPLE EXISTS  (REQUIRED if claiming EQUIVALENT)
For every test in FAIL_TO_PASS ∪ PASS_TO_PASS that touches the change surface,
the trace above shows identical pass/fail. No untested-behavior speculation.

FORMAL CONCLUSION
By Definition D1:
  - Test outcomes with Patch 1: [PASS/FAIL for each test]
  - Test outcomes with Patch 2: [PASS/FAIL for each test]
  - Since outcomes are [IDENTICAL/DIFFERENT], patches are
    [EQUIVALENT / NOT EQUIVALENT] modulo the existing tests.

ANSWER: [YES / NO]
```

## Common slip: name shadowing

When code calls `format(...)` (or any common name), do not assume Python's builtin / Node's global. Grep for `def format` / `function format` / `const format` in the same module first. The paper's motivating example (django-13670) catches an `AttributeError` that all standard reasoning missed because `format` was shadowed by a module-level helper.

## Tone

Skip prose recap before the certificate. Open straight to `SEMI-FORMAL PROOF OF PATCH EQUIVALENCE` and fill it.
