---
name: peep
description: Use when reasoning rigorously about code — comparing patches, finding bugs, explaining behavior, reviewing changes, OR planning new code in an existing or fresh project. Forces a structured certificate (premises, traced evidence with file:line citations, counterexample-or-proof, formal conclusion) instead of freewheeling chain-of-thought. Triggers include "peep", "analyze this", "are these equivalent", "find the bug", "why does this fail", "explain this code", "code review", "verify this patch", "design this feature", "add this to the codebase", "build this from scratch", "implement this in the existing project", "implement this in a new project", "plan this change". Use whenever the answer matters and a wrong answer would be expensive — even if the user did not explicitly ask for "rigorous" analysis.
---

# Peep — Semi-formal Code Reasoning

Based on Ugare & Chandra, *Agentic Code Reasoning* (Meta, 2026, arXiv:2603.01896v2). Semi-formal reasoning improves agentic code accuracy by **5–12 percentage points** over standard reasoning across patch equivalence, fault localization, and code question answering. This skill extends the paper's three analysis templates with two construction templates (brownfield and greenfield).

## Core principle

**You must fill in a structured certificate before reaching any conclusion.** The certificate forces explicit premises, traced evidence with `file:line` citations, a counterexample-or-proof step, and a formal conclusion grounded in the evidence above. Filling it out *is* the analysis. If it feels tedious, you're doing it right.

## Pick the right template

Match the task to the template. **Read only the matched template.** Do not load others.

| Task | Template |
|---|---|
| Compare two patches; verify a generated patch matches a reference; check if a change preserves test outcomes | `templates/patch-equivalence.md` |
| Find a bug; explain a test failure; identify buggy lines; root-cause analysis | `templates/fault-localization.md` |
| Explain how code works; answer "what does X do"; architectural questions; code review without a specific change | `templates/code-qa.md` |
| Add a feature to an EXISTING codebase (any non-empty project — there are existing files, callers, tests, conventions) | `templates/brownfield-construction.md` |
| Build something in a FRESH project (no existing code, no callers, no tests, no conventions to honor) | `templates/greenfield-construction.md` |

**Construction split rationale**: brownfield's dominant uncertainty is *existing-system uncertainty* (what already happens, what invariants are implicit, what callers expect); greenfield's is *design-space uncertainty* (what should exist, which dependencies, what verification harness). Filling brownfield sections like "invariants to preserve" and "backward-compat trace" with "n/a" in a fresh project creates false confidence and silently skips the real greenfield work — architecture choice and verification scaffolding. See `references/failure-modes.md` for the empirical case.

## Universal rules of engagement

These apply to every template.

1. **Read the source. Always.** Before filling any field, use grep/read to find the actual code or paste-in. Never populate from memory or training data.
2. **Trace function calls — don't guess.** If code calls `format()`, grep for `def format` in the module first. Check name resolution rules (Python: local → enclosing → module → builtins; JS: lexical scope → module → globalThis). Check for shadowing.
3. **Every claim needs a `file:line` citation.** "This function returns X" is not acceptable. "This function returns X (`src/auth.py:142`)" is.
4. **Flag uncertainty explicitly.** If you cannot read a third-party library's source, write: `ASSUMPTION: [library.function] does [X] based on name/docs. Source not verified.`
5. **Counterexample or proof — not opinion.** When concluding, exhibit a concrete failing case OR prove no such case exists. "I think it's correct" is not a conclusion.

## Three universal failure modes (from the paper)

1. **Incomplete execution tracing** — assuming function behavior without following the actual call chain. Fix: grep, read, trace.
2. **Third-party library semantics** — guessing what a library function does from its name. Fix: read the source if available; otherwise flag the assumption.
3. **Dismissing subtle differences** — identifying a semantic difference but concluding it doesn't matter. Fix: trace the difference to a concrete test outcome or input.

Templates surface additional task-specific failure modes. The full catalog with empirical citations is in `references/failure-modes.md`.

## Deep modules (read on demand from a template)

Templates point you to references when you need depth. Don't preload — open them only when the matched template tells you to.

| File | When to open |
|---|---|
| `references/failure-modes.md` | When you want the full catalog of failure modes a template guards against, with empirical citations. |
| `references/exploration-loop.md` | When the template asks you to *explore* an unfamiliar codebase before concluding (HypoExplore-style hypothesis loop with confidence thresholds). |
| `references/claim-types.md` | When you're filling CLAIM fields and need the inference-rule taxonomy (PCRLLM / ProofSketcher style: spec-decomposition, pattern-reuse, invariant-preservation, etc.). |
| `references/refinement-vocabulary.md` | When a construction template uses terms like *refinement*, *over-refinement*, *wp/sp*, *contract*, *minimality* — Dijkstra's predicate-transformer semantics and design-by-contract. |
| `references/citations.md` | When you need to cite the literature in a report or want to follow up on a specific source. |

## Construction templates produce TWO deliverables

Brownfield and greenfield templates each end with a mandatory `MENTAL MODEL DIAGRAM` step. After the prose certificate is filled, the agent must articulate the architecture **in their own words** as an `imagegen` brief and render it. Both files (`mental-model.brief.md` and `mental-model.png`) are saved alongside the prose plan.

The brief — not the image — is the primary review artifact. Its purpose is to surface the architectural intuitions that prose leaves implicit (purity vs IO, owned vs external, in-scope vs explicitly-rejected, invariants the picture must encode, anti-claims the picture must NOT imply). An adversarial reviewer reads the brief AND looks at the image to spot business-logic errors and hidden assumptions the prose hid. Do not write the brief from a checklist; the agent producing the certificate writes it themselves.

## Construction templates also SELF-ARCHIVE (v2.3)

Brownfield and greenfield certificates end with a mandatory `SELF-ARCHIVE` step that:

- computes `peepID = sha8(verbatim SPEC)` — content-addressed, deterministic
- writes `~/peep-archive/<peepID>/{spec.txt, contract.md, mental-model.brief.md, mental-model.png}` to a worktree of the orphan branch `peep` in `david-kijko/david-harness`
- commits and pushes the orphan branch immediately
- declares `UI_BEHAVIOR_AFFECTING: yes|no` so the downstream `checkit` skill knows whether `proofshot` is mandatory for the verification

The orphan branch IS the peep log: a permanent, diffable trail joining every contract to every verification of it (verifications produced by `/checkit <peepID>`).

## Tone

Skip prose recap. Fill the certificate. The bracketed fields ARE the work product.
