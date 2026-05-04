# Refinement Vocabulary

The construction templates use a small formal vocabulary borrowed from refinement calculus, predicate transformer semantics, and design-by-contract. This file explains those terms so you can use them precisely (and so the certificate's FORMAL CONCLUSION isn't hand-wavy).

## Refinement and over-refinement

**Refinement** is the formal relation between a specification and an implementation: `spec ⊑ impl` means impl satisfies spec. This is the partial order at the heart of the refinement calculus (Back & von Wright, *Refinement Calculus*, 1998).

**Over-refinement** (Sciencedirect 2002, *Requirements, specifications, and minimal refinement*) is when an implementation does *more* than the spec requires. In agent code-writing terms: every line of code, every dependency, every concept that doesn't trace back to a stated requirement is over-refinement.

Why care about the distinction:
- An under-refined implementation fails the spec (some Rn is unsatisfied).
- An over-refined implementation passes the spec but adds risk, cost, and surface area for bugs.

The construction templates' D2 (MINIMAL) is exactly an over-refinement check: every CHANGE SURFACE / CREATED SURFACE row must discharge at least one Rn / Cn / IC. A row that doesn't is over-refinement and must be removed.

## Predicate transformer semantics (wp / sp)

Dijkstra's predicate transformer semantics (1976, *A Discipline of Programming*) defines two functions on a program statement S:

- **wp(S, Q)** — the *weakest precondition*: the largest predicate P such that `{P} S {Q}` holds. "What must be true beforehand for S to guarantee Q after?"
- **sp(S, P)** — the *strongest postcondition*: the smallest predicate Q such that `{P} S {Q}` holds. "What's the most we can guarantee after S, given P beforehand?"

For peep purposes you don't need to compute these formally. You use the *intuition*:
- When verifying that planned code C satisfies Rn, ask: "what's the weakest precondition under which C produces Rn?" If that precondition is more than what callers actually provide, C is insufficient.
- When checking sufficiency in COUNTEREXAMPLE / SUFFICIENCY CHECK, the soundness sketch is essentially "I can show wp(C, Rn) is implied by what callers guarantee."

This is more rigorous than "C looks like it does Rn".

## Design-by-contract

Bertrand Meyer's contract methodology (Eiffel, 1988) attaches three things to each interface:
- **Pre**: what the caller must guarantee before calling.
- **Post**: what the implementation guarantees on return.
- **Inv** (invariant): what is true before and after every public method call on an object.

The greenfield template's INITIAL CONTRACTS AND INVARIANTS section is direct design-by-contract: declare the contract you are creating, with Pre / Post / Errors made explicit.

The brownfield template's INVARIANTS THAT MUST BE PRESERVED is the invariant half of design-by-contract applied retroactively: discover the implicit invariants the existing system maintains, then prove your change preserves them.

## Correct-by-construction (CbC)

Correct-by-construction (sometimes "deductive synthesis") is the methodology where program development proceeds as: spec → implementation → proof, with each step justified by the spec. Examples in the literature: Fiat (Coq, MIT, 2014), Synquid (program synthesis from polymorphic refinement types, 2016), Cobblestone (divide-and-conquer formal verification, 2025).

The construction templates are *informal* CbC certificates. We don't translate to Lean or Coq, but we use the same skeleton:
1. Decompose the spec into atomic Rn.
2. Plan the implementation, mapping each Rn → code.
3. Discharge proof obligations: each Rn has a soundness sketch or a counterexample.
4. Conclude formally against the four definitions (D1–D4).

The benefit isn't formal correctness — it's that the *skeleton* of formal correctness eliminates a class of mistakes (under-refinement = missed Rn; over-refinement = scope creep) that informal "vibe-driven" construction makes constantly.

## Soundness, completeness, sufficiency, minimality

These four words are easy to confuse. The construction templates use them as follows:

- **Sufficient** (D1): every Rn has a code mapping. Equivalent to "no missed requirement" — under-refinement is impossible.
- **Minimal** (D2): every code change has an Rn. Equivalent to "no extra requirement invented" — over-refinement is impossible.
- **Sound** (used in soundness sketches): if the planned code runs without error, Rn holds. ("If P then Q" — no false positives.)
- **Complete** (used implicitly in counterexample search): every input that should satisfy Rn does satisfy Rn. ("If Q should hold then P satisfies it" — no false negatives.)

The COUNTEREXAMPLE / SUFFICIENCY CHECK section asks for soundness (sketch) OR a counterexample to soundness (input where Rn fails). Completeness is implicit in the test partitions you cover.

## Compatibility (brownfield) vs Coherence (greenfield)

The construction templates split FORMAL CONCLUSION's compatibility check by domain:

- **Brownfield D3 — COMPATIBLE**: external. Existing callers preserved, PASS_TO_PASS tests still green. Compatibility is a relation between the change and the existing system.
- **Greenfield D3 — INTERNALLY COHERENT**: internal. The chosen interfaces, data model, runtime assumptions, and verification strategy don't contradict one another. There's no "existing system" to be compatible with — the system is what you're creating, so coherence is among its parts.

This distinction matters because it's the structural reason the two construction templates can't be one. A greenfield certificate trying to satisfy "compatible" with nothing creates false confidence (failure mode G3 surface — "compatible: yes, no callers exist" silently skips the verification scaffold check).

## Citations

- Back & von Wright (1998), *Refinement Calculus: A Systematic Introduction*, Springer.
- Sciencedirect 2002, *Requirements, specifications, and minimal refinement*.
- Dijkstra (1976), *A Discipline of Programming*, Prentice-Hall.
- Wikipedia, *Predicate transformer semantics*.
- Meyer (1988), *Object-Oriented Software Construction*, Prentice-Hall (Eiffel design-by-contract).
- Chlipala et al. (2014), *Fiat: Deductive Synthesis*, MIT.
- Polikarpova et al. (2016), *Program synthesis from polymorphic refinement types*, PLDI.
- Kasibatla et al. (2025), *Cobblestone: Divide-and-Conquer Formal Verification*.
