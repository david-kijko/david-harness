# Template: Fault Localization

**Use when**: finding bugs, explaining test failures, identifying buggy lines, root-cause analysis. Especially when the test crashes/asserts at one site but the actual bug is upstream (the most common failure mode in real localization).

**Failure modes this template guards against** (full catalog in `references/failure-modes.md`):
- Stopping at the crash site instead of tracing upstream to the root cause
- Indirection bugs (bug lives in a class the test doesn't directly invoke)
- Multi-file bugs that span 2+ locations
- Domain-specific bugs (numerical, concurrency) where pattern-matching fails

This template requires hypothesis-driven exploration. Use `references/exploration-loop.md` for the HYPOTHESIS → EVIDENCE → OBSERVATION → CONFIRMED/REFUTED/REFINED loop with confidence thresholds. Use `references/claim-types.md` for tagging claims by inference type.

---

## Fill the certificate. Read every file you cite.

```
SEMI-FORMAL FAULT LOCALIZATION CERTIFICATE

TASK
Failing test: [test_file:line]
Test source (the assertions and what they check): [paste or summarize verbatim]
Available source files: [list — files the test loads or transitively reaches]

PHASE 1 — TEST SEMANTICS (state as formal premises)
T1: The test calls [Class.method(args)] expecting [behavior]
T2: The test asserts [condition] / expects exception [type]
T3: Observed failure mode (if known): [behavior vs expectation]

REACHABILITY GATE  (mandatory — guards against fabricated state assumptions)
For each premise about test STATE that is not literally constructed in the
test body, you MUST cite the file:line in the prompt that establishes how
the state arrives. If the prompt does not contain that evidence, the premise
is a hypothesis and MUST be tagged `(hypothesis — unverified)`.

  S1: [State assumption — e.g. "the PercentOff instance has been .apply()'d before"]
       Evidence in prompt: [file:line cite, OR "none — flagged as hypothesis"]
       Status: [VERIFIED / hypothesis — unverified]

Common traps caught here:
- "shared fixture" / "module-level singleton" / "session-scoped pytest fixture"
   theories — these only hold if the prompt actually shows the fixture or
   sharing. If the failing test calls `Foo()` inline, the agent CANNOT assume
   the same `Foo` instance is shared across the suite without evidence.
- "test pollution from prior test" — same: needs evidence of mutating state.
- "race condition under -n N workers" — same: needs evidence of concurrent
   access to shared mutable state, not just "pytest-xdist is in use".

If your final RANKED PREDICTIONS depend on an S[N] tagged unverified, the
prediction must inherit `(depends on hypothesis S[N])` and you must list
what evidence would upgrade it to VERIFIED.

PHASE 2 — CODE PATH TRACING
Build the call sequence from test → production code. For each significant call:
  METHOD: [Class.method(params)]
  LOCATION: [file:line]
  BEHAVIOR: [what this method actually does — read it]
  RELEVANT: [why it matters to T1/T2/T3]

(Use the exploration loop in `references/exploration-loop.md` if you must hunt
through the codebase. Maintain a hypothesis memory bank: H1, H2, H3 with
confidence updates as you read more.)

PHASE 3 — DIVERGENCE ANALYSIS
For each suspicious region, state where implementation diverges from test
expectations as a numbered claim, citing both a premise and a code location.

CLAIM D1: At [file:line], [code description] would produce [behavior]
          which contradicts PREMISE T[N] because [reason]
CLAIM D2: ...
(Each claim must reference a specific PREMISE and a specific code location.
Inference-rule taxonomy: see `references/claim-types.md`.)

SUSPICIOUS REGIONS
Region R1: [file:lines]
  Code (paste the exact lines): [...]
  Hypothesis: This causes failure because [reason tied to D[N]]
  Trace from test: T1 → ... → R1 when [condition]
  Verdict: [LIKELY BUGGY / UNLIKELY / UNCERTAIN]
  Evidence: [file:line citations supporting the verdict]
Region R2: ...

PHASE 4 — RANKED PREDICTIONS  (most likely first)
1. [file:lines] — Confidence: [HIGH / MEDIUM / LOW]
   Because: [reason — must cite a CLAIM D[N]]
2. [file:lines] — Confidence: [...]
   Because: [...]
3. ...

DIFFERENTIAL CHECK  (REQUIRED — protects against stopping at crash site)
"If the bug were at [crash site] rather than [predicted root cause], what
should we observe that we don't?" → [Specific testable difference, with
file:line citations on either side.]

FORMAL CONCLUSION
The most likely fault is [file:lines] because [traced execution shows this
code produces incorrect behavior under the test's input, specifically:
evidence from CLAIM D[N] and the differential check above].
```

## Common slip: stopping at the crash site

A `StackOverflowError` at line 185 is not the bug — it's the symptom. The bug is upstream, in whatever set up the recursive condition. The Mockito_8 case study in the paper (Appendix C) shows the agent must trace 2+ turns back from the crash to find the registration overwrite at line 80. The differential check section above forces this discipline.

## Common slip: only inspecting the directly-invoked class

If `test_csv_parsing` calls `CSVParser.parse()` and the bug is in `CSVFormat.withHeader()`, standard reasoning will fixate on `CSVParser`. The exploration loop's hypothesis memory bank (`references/exploration-loop.md`) prevents this — H1 ("bug is in directly-invoked class") gets REFUTED by evidence, freeing the agent to explore indirection.

## Tone

Skip prose. Open straight to `SEMI-FORMAL FAULT LOCALIZATION CERTIFICATE` and fill it.
