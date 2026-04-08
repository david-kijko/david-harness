---
name: peep
description: Semi-formal code reasoning skill. Forces structured certificate-based analysis instead of freewheeling chain-of-thought. Use when comparing patches/diffs, localizing bugs/faults, answering code understanding questions, reviewing code, or any task requiring rigorous semantic analysis of source code. Triggers include "peep", "analyze this code", "are these equivalent", "find the bug", "why does this fail", "explain this function", "code review", "verify this patch".
---

# Peep: Semi-formal Agentic Code Reasoning

Based on: "Agentic Code Reasoning" (Ugare & Chandra, Meta, 2026, arXiv:2603.01896v2)

Semi-formal reasoning improves agentic code analysis accuracy by 5-12 percentage points over standard reasoning across patch equivalence, fault localization, and code question answering tasks.

## Core Principle

**You must fill in a structured certificate before reaching any conclusion about code.**

The certificate forces you to:
1. State explicit premises (what the code does, not what you think it does)
2. Trace execution paths through actual function calls (grep, read the source — never guess)
3. Cite file:line evidence for every claim
4. Provide a counterexample OR prove none exists
5. Write a formal conclusion grounded in the evidence above

You CANNOT skip sections. You CANNOT make claims without traced evidence. If you cannot trace a path, say so — do not guess from function names.

## Three Failure Modes to Prevent

1. **Incomplete execution tracing**: Assuming function behavior without following the actual call chain. ALWAYS grep for the definition, read it, and trace what it actually does.
2. **Third-party library semantics**: Guessing what a library function does from its name. If source is unavailable, explicitly state the assumption and flag uncertainty.
3. **Dismissing subtle differences**: Identifying a semantic difference but incorrectly concluding it doesn't matter. If you find a difference, trace it to a concrete test outcome.

## How to Use

Select the certificate template that matches your task. Fill in EVERY bracketed field. Read actual source code to populate the fields — do not reason from memory or training data alone.

---

## Template 1: Patch Equivalence Verification

Use when: comparing two patches/diffs, checking if a generated patch matches a reference, verifying code changes produce the same behavior.

```
SEMI-FORMAL PROOF OF PATCH EQUIVALENCE

DEFINITIONS:
D1: Two patches are EQUIVALENT MODULO TESTS iff executing the
    existing repository test suite produces identical pass/fail
    outcomes for both patches.
D2: The relevant tests are ONLY those in FAIL_TO_PASS and
    PASS_TO_PASS (the existing test suite in the repository).

PREMISES (state what each patch does):
P1: Patch 1 modifies [file(s)] by [specific change description]
P2: Patch 2 modifies [file(s)] by [specific change description]
P3: The FAIL_TO_PASS tests check [specific behavior being tested]
P4: The PASS_TO_PASS tests check [specific behavior, if relevant]

ANALYSIS OF TEST BEHAVIOR:

For FAIL_TO_PASS test(s):
  Claim 1.1: With Patch 1 applied, test [name] will [PASS/FAIL]
             because [trace through the code behavior]
  Claim 1.2: With Patch 2 applied, test [name] will [PASS/FAIL]
             because [trace through the code behavior]
  Comparison: [SAME/DIFFERENT] outcome

For PASS_TO_PASS test(s) (if patches could affect them differently):
  Claim 2.1: With Patch 1 applied, test behavior is [description]
  Claim 2.2: With Patch 2 applied, test behavior is [description]
  Comparison: [SAME/DIFFERENT] outcome

EDGE CASES RELEVANT TO EXISTING TESTS:
(Only analyze edge cases that the ACTUAL tests exercise)

E1: [Edge case that existing tests exercise]
  - Patch 1 behavior: [specific output/behavior]
  - Patch 2 behavior: [specific output/behavior]
  - Test outcome same: [YES/NO]

COUNTEREXAMPLE (required if claiming NOT EQUIVALENT):
Test [name] will [PASS/FAIL] with Patch 1 because [reason]
Test [name] will [FAIL/PASS] with Patch 2 because [reason]
Therefore patches produce DIFFERENT test outcomes.

OR

NO COUNTEREXAMPLE EXISTS (required if claiming EQUIVALENT):
All existing tests produce identical outcomes because [reason]

FORMAL CONCLUSION:
By Definition D1:
- Test outcomes with Patch 1: [PASS/FAIL for each test]
- Test outcomes with Patch 2: [PASS/FAIL for each test]
- Since test outcomes are [IDENTICAL/DIFFERENT], patches are
  [EQUIVALENT/NOT EQUIVALENT] modulo the existing tests.

ANSWER: [YES/NO]
```

---

## Template 2: Fault Localization

Use when: finding bugs, explaining test failures, identifying buggy lines, root cause analysis.

```
SEMI-FORMAL FAULT LOCALIZATION CERTIFICATE

TASK:
Given failing test [test name] in [repository], identify the buggy
code region(s) causing the failure.

AVAILABLE INFORMATION:
- Failing test: [test file:line]
- Test source: [key assertions and what they check]
- Loaded source files: [list files the test touches]

SUSPICIOUS REGIONS:

Region R1: [file:lines]
  Code: [the actual code]
  Hypothesis: This region could cause test failure because [reason]
  Trace: Test calls [function] -> which calls [function] -> which
         reaches this region when [condition]
  Verdict: [LIKELY BUGGY / UNLIKELY / UNCERTAIN]
  Evidence: [specific file:line citations]

Region R2: [file:lines]
  Code: [the actual code]
  Hypothesis: [reason this could be buggy]
  Trace: [execution path from test to this region]
  Verdict: [LIKELY BUGGY / UNLIKELY / UNCERTAIN]
  Evidence: [specific file:line citations]

[Continue for all suspicious regions]

RANKED PREDICTIONS (most likely first):
1. [file:lines] — Confidence: [HIGH/MEDIUM/LOW] — Because: [reason with evidence]
2. [file:lines] — Confidence: [HIGH/MEDIUM/LOW] — Because: [reason with evidence]
3. [file:lines] — Confidence: [HIGH/MEDIUM/LOW] — Because: [reason with evidence]

FORMAL CONCLUSION:
The most likely fault location is [file:lines] because [traced
execution path shows that this code produces incorrect behavior
when the test exercises condition X, specifically: evidence].
```

---

## Template 3: Code Question Answering

Use when: explaining how code works, answering "what does X do", architectural questions, code review, understanding behavior.

```
SEMI-FORMAL CODE ANALYSIS CERTIFICATE

QUESTION: [the question being answered]

FUNCTION TRACE TABLE:
| Function | File:Line | Verified Behavior | Key Detail |
|----------|-----------|-------------------|------------|
| [name]   | [path:N]  | [what it actually does — READ the source] | [edge case or caller] |
| [name]   | [path:N]  | [verified behavior] | [detail] |

DATA FLOW ANALYSIS:
- Variable [name] is initialized at [file:line] as [value/type]
- It flows through [function] at [file:line] where [transformation]
- It reaches [function] at [file:line] where [final use]
- Key constraint: [what must be true for correct behavior]

SEMANTIC PROPERTIES (with evidence):
SP1: [Property claim] — Evidence: [file:line shows X]
SP2: [Property claim] — Evidence: [file:line shows X]
SP3: [Property claim] — Evidence: [file:line shows X]

ALTERNATIVE HYPOTHESIS CHECK:
Could the answer be [alternative interpretation]?
- Check: [what would need to be true]
- Finding: [file:line shows this is/isn't the case]
- Result: [CONFIRMED alternative / RULED OUT]

GROUNDED ANSWER:
[Answer the question, citing only the traced evidence above.
Every claim must reference a specific file:line from the trace table.]
```

---

## Rules of Engagement

1. **Always read the source.** Before filling any field, use grep/read to find the actual code. Never populate from memory.
2. **Trace function calls, don't guess.** If code calls `format()`, grep for `def format` in the module. Python name resolution: local -> enclosing -> module -> builtins. Check for shadowing.
3. **Every claim needs a file:line citation.** "This function returns X" is not acceptable. "This function returns X (src/auth.py:142)" is.
4. **Flag uncertainty explicitly.** If you cannot read a third-party library's source, write: "ASSUMPTION: [library.function] does [X] based on name/docs. Source not verified."
5. **Do not shortcut.** The certificate exists because shortcuts cause errors. Filling it out IS the analysis. If it feels tedious, you're doing it right.
6. **Counterexample or proof, not opinion.** When concluding, you must either show a concrete failing case OR prove no such case exists. "I think they're equivalent" is not a valid conclusion.
