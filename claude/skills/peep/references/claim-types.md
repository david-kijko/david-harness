# Claim Types — Inference-Rule Taxonomy

When a template asks you to "tag each CLAIM by inference type", use the categories below. The taxonomy is adapted from PCRLLM (Proof-Carrying Reasoning with LLMs, arxiv 2511.08392) and ProofSketcher (arxiv 2604.06401), both of which improve LLM reasoning accuracy by forcing each step to declare which inference rule it's using.

## Why tag claims at all

Untagged claims look uniform on the page but rest on very different evidence. "X follows from Y" can mean any of: a direct read of source, a structural property of the type system, a contract obligation, an empirical trace, an analogy from another module. Mixing these silently produces fragile reasoning. Naming the inference type forces you to check that the rule actually applies.

## The taxonomy

### 1. `empirical-from-trace`
**The claim follows from running code or reading literal source.**
Use when: you grep'd, read a file, or executed a script, and the claim is what you observed.
Example: `CLAIM: format() at src/dateformat.py:340 expects a datetime, not an int. (empirical-from-trace, src/dateformat.py:340-348)`

### 2. `by-construction`
**The claim follows from how the code is structured to begin with.**
Use when: a claim about new code you're planning. The property holds *because* of the design decision, not because you observed runtime behavior.
Example: `CLAIM: tenant_id is never null in the Order table. (by-construction — schema declares NOT NULL at migrations/0042_orders.sql:8)`

### 3. `by-invariant`
**The claim follows from a system-wide invariant you've identified.**
Use when: invariants from `INVARIANTS THAT MUST BE PRESERVED` section justify the claim.
Example: `CLAIM: after this change, every Session row still has a non-null user_id. (by-invariant INV2 — preserved because new code only inserts via SessionFactory, which requires user_id at src/auth/session.py:55)`

### 4. `by-contract`
**The claim follows from a declared pre/postcondition or interface contract.**
Use when: contracts in `INITIAL CONTRACTS AND INVARIANTS` (greenfield) or interface specifications (brownfield) justify the claim.
Example: `CLAIM: the parser returns a non-empty list when input is non-empty. (by-contract IC1 — postcondition declared at src/parse/parser.py:12)`

### 5. `by-pattern-reuse`
**The claim follows from reusing an existing pattern whose properties are known.**
Use when: brownfield work where a survey row was decided REUSE.
Example: `CLAIM: the Foo client now retries on 5xx with exponential backoff. (by-pattern-reuse — wraps with util/retry:with_retry which has documented behavior at src/util/retry.py:14-40)`

### 6. `by-spec-decomposition`
**The claim is one atomic Rn extracted from the user's spec.**
Use when: SPEC DECOMPOSITION rows; tagging a code mapping as "this discharges Rn".
Example: `CLAIM: when the user clicks Cancel, the dialog closes within 100ms. (by-spec-decomposition R3 — verbatim from user requirement)`

### 7. `by-counterexample-search`
**The claim follows from failing to find a counterexample after a sound search.**
Use when: COUNTEREXAMPLE / SUFFICIENCY CHECK section, when claiming sufficiency by absence.
Example: `CLAIM: no input violates R2. (by-counterexample-search — generated 100 random inputs spanning [empty, single-char, multi-line, malformed-utf8] partitions; all pass)`

### 8. `assumption-flagged`
**The claim is unverified — flag explicitly.**
Use when: you cannot read a third-party library's source, or the claim depends on undocumented behavior.
Example: `CLAIM: requests.post() with timeout=30 raises Timeout after 30s. (assumption-flagged — based on requests docs; not verified against source)`

## How to use the tags

In the certificate, append the tag in parentheses after each CLAIM line:

```
CLAIM D1: At src/csv/format.py:88, with_header() raises ParseException
          when header_row.split(',') yields a single empty string,
          which contradicts PREMISE T2 (test expects parse to succeed
          on input with leading newline).
          (empirical-from-trace, src/csv/format.py:88-105)
```

```
R3 → satisfied by src/auth/middleware.py:45-78 because the new
     middleware reads tokens from headers, validates expiry,
     and rejects with 401 on failure.
     (by-spec-decomposition R3 ∧ by-construction)
```

```
SP1: The map is pre-populated with all valid SliceType values.
     Evidence: QtReflEventView.h:69-73 initializes with 4 mappings.
     toggleSlicingOptions only assigns from the SliceType enum.
     (empirical-from-trace ∧ by-construction)
```

## When NOT to tag

If the certificate is short and the inference type is obvious from the section it lives in (e.g., everything in PHASE 1 of fault-localization is `by-spec-decomposition` of the test), skip the tags. The point of tags is to surface ambiguity, not to add ceremony.

The tags are also unnecessary in CHANGE SURFACE rows (where every row is implicitly `by-spec-decomposition` of the cited Rn) and in EXISTING PATTERN SURVEY rows (which are inherently `empirical-from-trace`).

## Anti-patterns

- **Tagging everything `empirical-from-trace`**: if your whole certificate looks like that, you're probably not making any non-trivial inferences. Consider whether the question even needs peep.
- **Tagging without citing**: a tag without a `file:line` cite or a referenced premise/contract/invariant means nothing.
- **Inventing new tag types**: if a claim doesn't fit one of the 8 above, the claim is probably mis-stated. Fix the claim, not the taxonomy.

## Citations

- PCRLLM: Proof-Carrying Reasoning with Large Language Models under Stepwise Logical Constraints (arxiv 2511.08392).
- ProofSketcher: hybrid design with explicit step types — rewrite, case split, induction, contradiction (arxiv 2604.06401).
- Theorem dependency mapping (research-agora): inspiration for treating premises as nodes and claims as edges.
