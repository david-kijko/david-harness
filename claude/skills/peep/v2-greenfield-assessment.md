# Peep v2 Greenfield Construction Assessment

## 1. Greenfield-readiness grade: 6/10

The proposed `brownfield-construction.md` template is partly greenfield-ready because requirements decomposition, change/code mapping, test obligations, and sufficiency checks are construction-universal. But most of its distinctive machinery assumes an existing system: local patterns, integration points, preserved invariants, callers, and regression tests. In a fresh project those sections tend to collapse into “none,” which can look complete while skipping the real greenfield work: choosing architecture, dependencies, module boundaries, contracts, and verification scaffolding. So the design would prevent some under-specification, but it would not reliably prevent over-engineered, arbitrary, or untestable foundations.

## 2. Section-by-section greenfield applicability table

| Brownfield section | Greenfield rating | Explanation |
|---|---|---|
| SPEC DECOMPOSITION | APPLIES_AS_IS | Atomic Rn requirements still anchor the work; greenfield needs them because there is no inherited behavior to disambiguate intent. |
| EXISTING PATTERN SURVEY | NEEDS_REPLACEMENT | No local patterns exist. Replace with an options/precedent survey: stack conventions, constraints, comparable minimal designs, and rejected alternatives. |
| INTEGRATION POINTS | APPLIES_DEGENERATE | Existing touchpoints disappear, but initial seams still matter: entrypoint, API boundary, storage boundary, test harness, and deployment boundary. |
| INVARIANTS THAT MUST BE PRESERVED | APPLIES_DEGENERATE | There are no preserved invariants, but the agent must define initial contracts: input/output guarantees, error semantics, state rules, and non-goals. |
| CHANGE SURFACE | APPLIES_AS_IS | Every created file should still be tied to Rn, a contract, or verification. It becomes “created surface,” not patch surface. |
| REQUIREMENT -> CODE MAPPING | APPLIES_AS_IS | Each Rn should map to concrete file:line evidence after code exists, including tests. |
| BACKWARD-COMPATIBILITY TRACE | VACUOUS_OR_NA | No callers or regression tests exist. Do not fill with empty ritual; replace with internal-coherence and future-migration risk only where relevant. |
| NEW TEST OBLIGATIONS | APPLIES_AS_IS | Essential in greenfield because the harness is not inherited; include creation of runnable verification commands. |
| COUNTEREXAMPLE / SUFFICIENCY CHECK | APPLIES_AS_IS | Still central. The basis shifts from “does not break old behavior” to “satisfies the spec under representative and adversarial inputs.” |
| FORMAL CONCLUSION | APPLIES_DEGENERATE | “Compatible” is mostly vacuous. Conclude sufficient, minimal, internally coherent, verifiable, and intentionally scoped. |

## 3. What truly differs in greenfield vs brownfield construction reasoning

1. **The dominant uncertainty changes.** Brownfield uncertainty is existing-system uncertainty: what already happens, which invariants are implicit, and where a change can safely attach. Greenfield uncertainty is design-space uncertainty: what should exist at all.

2. **The agent must invent the reference frame.** Brownfield usually gives naming, layering, dependencies, test style, error conventions, and deployment shape. Greenfield requires choosing those foundations and justifying them from requirements and constraints rather than taste.

3. **Minimality has a different burden.** Brownfield minimality means the smallest safe change surface. Greenfield minimality means the fewest concepts, layers, dependencies, and extension points that satisfy the requirements while remaining verifiable.

4. **Verification infrastructure is part of the feature.** Brownfield work can usually extend existing tests. Greenfield work must create the harness: unit/integration test setup, smoke command, fixtures, build/type/lint commands, and a runnable user path.

5. **Failure modes diverge.** Greenfield-only risks include premature abstraction, framework-of-the-week selection, untestable boundaries, invented future requirements, inconsistent contracts, and no runnable path. Brownfield-only risks include invariant violation, deprecated-pattern reuse, caller breakage, semantic drift, and regression-test overfitting.

6. **Evidence changes type.** Brownfield certificates rely heavily on existing file:line evidence. Greenfield still needs file:line evidence after construction, but before construction it needs explicit design claims, assumptions, constraints, and rejected alternatives.

7. **Compatibility becomes coherence.** Brownfield compatibility is compatibility with existing APIs, data, callers, and tests. Greenfield compatibility is coherence among newly chosen interfaces, data model, runtime assumptions, and verification strategy.

## 4. Recommendation: two templates sharing common references

I recommend option (b): keep `brownfield-construction.md` and add `greenfield-construction.md`, with common references. Progressive disclosure makes the token cost of an extra template low because only the matched template loads. The benefit is high because the certificate questions differ: brownfield asks whether a feature preserves an existing system; greenfield asks whether the initial system design is justified, minimal, and verifiable.

A single conditional `construction.md` would either bloat every construction invocation with many skip branches or blur the router distinction between “modify an existing system” and “create a new one.” That confusion is costly. Empty brownfield fields such as “no callers” and “no invariants” can create false confidence while omitting architecture selection, dependency minimality, and verification bootstrapping.

## 5. Greenfield-specific template sketch

Suggested `templates/greenfield-construction.md` sections:

1. **SPEC DECOMPOSITION** — Atomic Rn requirements, non-goals, and open assumptions.
2. **CONSTRAINTS AND CONTEXT** — Runtime, language, deployment, persistence, security, performance, and user-imposed constraints.
3. **DESIGN OPTIONS CONSIDERED** — Plausible implementation shapes plus rejected alternatives and reasons.
4. **MINIMAL ARCHITECTURE DECISION** — Chosen modules, boundaries, dependencies, and why no simpler design suffices.
5. **INITIAL CONTRACTS AND INVARIANTS** — Public interfaces, data contracts, error semantics, state rules, and lifecycle assumptions.
6. **CREATED SURFACE** — Every created file/artifact tied to Rn, a contract, or verification scaffolding.
7. **REQUIREMENT -> CODE MAPPING** — Each Rn mapped to file:line implementation and test evidence.
8. **VERIFICATION SCAFFOLD** — Test framework, smoke command, build/type/lint command, fixture strategy, and run instructions.
9. **NEW TEST OBLIGATIONS** — NTn cases for each Rn, including negative cases and one user-visible path.
10. **COUNTEREXAMPLE / SUFFICIENCY CHECK** — Per-Rn proof sketch or concrete counter-input; include design-level counterexamples.
11. **FORMAL CONCLUSION** — Sufficient, minimal, internally coherent, verifiable, intentionally scoped.

Use `failure-modes.md`, `exploration-loop.md`, `claim-types.md`, `refinement-vocabulary.md`, and `citations.md`, but weight them differently. Greenfield should lean most on failure modes, exploration, and refinement vocabulary for design search, over-refinement detection, and contracts. `claim-types.md` should distinguish requirement, design, and behavioral claims. `citations.md` remains useful, but brownfield-specific examples should not dominate.

## 6. Adversarial check

1. **Premature abstraction.** A one-command JSON-to-CSV CLI becomes `ApplicationService`, `CommandBus`, `Repository`, `SerializerFactory`, and plugin registries. Brownfield change-surface accounting records the files but does not challenge whether the concepts are necessary.

2. **Unjustified dependency choice.** A static landing page is scaffolded with SSR, ORM, auth, and queues because no existing pattern contradicts it. Greenfield needs explicit options and dependency-minimality checks.

3. **No runnable verification path.** The agent writes feature files and tests but no package scripts, fixtures, or smoke command. Brownfield assumes existing machinery; greenfield must require verification scaffolding as a deliverable.
