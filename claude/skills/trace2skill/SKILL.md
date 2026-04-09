---
name: trace2skill
description: Use when analyzing .codex or .claude session traces to extract transferable lessons, emit reusable skill patches, or merge trace-derived SoPs into a target skill.
---

# Trace2Skill: Session Trace Analyst

> **Scope:** Extract generalizable, transferable lessons from `.codex` and `.claude`
> coding-session traces. Produce structured skill patches that can be merged into
> domain-specific skill documents.

## 1. Definitions and Conventions

| Term | Meaning |
|---|---|
| **Trace** | A complete serialized session: system prompt, user turns, assistant turns (reasoning + tool calls + observations), and outcome. |
| **Outcome Label** | `success` if the session's final artifact satisfies the user's intent and passes any available verification; `failure` otherwise. `ambiguous` if no ground truth is available and intent satisfaction cannot be determined. |
| **Patch** | A structured JSON object proposing one or more edits to a target skill document. |
| **SoP** | Standard Operating Procedure — a reusable, declarative rule the target agent should follow. |
| **Target Skill** | The skill document that patches will be applied to. It may be an existing human-written skill or an empty scaffold. |

## 2. Trace Format Contract

The analyst agent MUST accept traces in any of these serialization formats and normalize internally before analysis. Do not reject a trace solely because of format differences.

### 2.1 Supported Serializations

**JSONL transcript** (preferred): Each line is a JSON object with at minimum:

```json
{
  "role": "user" | "assistant" | "system" | "tool",
  "content": "<text>",
  "tool_calls": [{"name": "...", "arguments": "..."}],
  "tool_output": "<stdout+stderr>",
  "timestamp_ms": 1717900000000,
  "turn_index": 0
}
```

**Markdown transcript**: Alternating `## User`, `## Assistant`, `## Tool Output` sections. Tool calls appear as fenced code blocks tagged with the tool name.

**Raw** `.claude` **/** `.codex` **export**: Platform-native JSON. The agent must locate the message array and map it to the canonical schema above. Known paths:

- `.claude`: `session.messages[]` with `.role`, `.content`, `.tool_use[]`
- `.codex`: `turns[]` with `.role`, `.content`, `.function_call`

### 2.2 Required Metadata Envelope

Every trace MUST be accompanied by (or the analyst must infer):

```json
{
  "trace_id": "<unique identifier>",
  "outcome": "success" | "failure" | "ambiguous",
  "domain_hint": "<e.g. 'web-frontend', 'data-pipeline', 'refactor'>",
  "model_id": "<e.g. 'claude-sonnet-4-20250514', 'o3-mini'>",
  "session_source": "codex" | "claude" | "other",
  "ground_truth": "<optional: expected final state or test command>",
  "user_intent_summary": "<one-sentence plain-language goal>"
}
```

If `outcome` is missing, the analyst MUST attempt to infer it from the final turn and any verification steps before proceeding. If inference confidence is low, label `ambiguous` and note the uncertainty in the patch reasoning.

## 3. Analyst Workflow

### 3.1 Pre-Analysis Normalization

1. Parse the trace into the canonical turn schema (§2.1).
2. Validate the metadata envelope (§2.2). Fill missing fields where possible.
3. Segment the trace into **phases**: intent clarification, planning, implementation, verification, delivery. A phase boundary occurs when the agent shifts from one activity to another (for example, stops writing code and begins running tests).
4. Tag each assistant turn with the phase label. This segmentation is used throughout the analysis and MUST appear in the patch reasoning.

### 3.2 Failure Analysis (Error Analyst)

> Applies when `outcome == "failure"`.

**Objective:** Identify the *causal chain* from a specific agent decision or omission to the incorrect outcome, and propose a patch that would prevent the same class of failure.

**Mandatory Steps:**

1. **Locate the failure surface.** What is concretely wrong in the final artifact? Diff against ground truth if available; otherwise state the observable symptom.
2. **Trace backward through phases.** For each phase, ask: did the agent have the information needed to act correctly? If yes, the error is a *decision error* in that phase. If no, trace further back to where the information was available but not propagated.
3. **Classify the root cause.** Use exactly one primary label:

   | Label | Definition |
   |---|---|
   | `wrong-tool-choice` | Agent selected an inappropriate tool or library for the subtask. |
   | `missing-verification` | Agent did not verify an intermediate or final result that would have caught the error. |
   | `incorrect-reasoning` | Agent's chain-of-thought contained a factual or logical error. |
   | `misunderstood-intent` | Agent misinterpreted the user's goal. |
   | `environment-mismatch` | Agent assumed an environment state (installed packages, file layout, OS) that did not hold. |
   | `silent-data-corruption` | A tool call succeeded but produced subtly incorrect output that the agent accepted. |
   | `context-window-loss` | Relevant earlier information was no longer attended to by the time of the critical decision. |
   | `premature-delivery` | Agent declared completion before all acceptance criteria were met. |
   | `other` | None of the above; provide a free-text sub-label. |

4. **Validate the diagnosis.** If you have tool access, implement a minimal fix and confirm it resolves the failure. If you lack tool access, describe the counterfactual fix and state that it is unvalidated. Patches from validated diagnoses receive a `confidence: high` tag; unvalidated ones receive `confidence: medium`.
5. **Generalize.** Rewrite the diagnosis as a domain-general SoP. The SoP must not reference the specific file names, variable names, or task details of this trace. It must describe *when* the rule applies, *what* the agent should do, and *why* skipping it causes failure.
6. **Quality gate.** If you cannot identify a causal chain with at least medium confidence, output `{"patch": null, "reason": "<explanation>"}` and stop. Do not propose speculative patches.

### 3.3 Success Analysis (Success Analyst)

> Applies when `outcome == "success"`.

**Objective:** Identify *reusable behavior patterns* that contributed to the correct outcome, especially behaviors that are non-obvious or that counteract known failure modes.

**Mandatory Steps:**

1. **Enumerate effective behaviors.** Walk through each phase and list every agent action that materially contributed to success. Focus on:
   - Verification steps the agent performed proactively.
   - Tool or library choices that avoided known pitfalls.
   - Information-gathering actions taken before committing to a plan.
   - Graceful recovery from intermediate errors.
2. **Filter for generalizability.** Discard behaviors that are trivially expected (for example, "the agent read the user's message") or task-specific (for example, "the agent used the correct regex for this particular log format"). Retain only behaviors that constitute a transferable *strategy*.
3. **Rank by prevalence potential.** Order the remaining behaviors by how likely they are to recur across diverse sessions. Broadly applicable patterns come first.
4. **Formulate SoPs.** Each retained behavior becomes a candidate SoP, written in the same when/what/why format as error-derived SoPs.

### 3.4 Ambiguous-Outcome Handling

When `outcome == "ambiguous"`:

- Run both the failure and success workflows.
- Tag every resulting SoP with `outcome_certainty: low`.
- During consolidation (§5), `low`-certainty SoPs require corroboration from at least two other traces to survive the merge.

## 4. Patch Format Specification (Contract)

Every analyst output MUST conform to this JSON schema. Non-conforming patches are rejected by the programmatic validator before reaching the merge stage.

```json
{
  "$schema": "trace2skill-patch-v1",
  "trace_id": "<string>",
  "outcome": "success" | "failure" | "ambiguous",
  "analyst_type": "error" | "success",
  "confidence": "high" | "medium" | "low",
  "root_cause_label": "<from §3.2 table, or null for success patches>",
  "phase": "<phase where the critical behavior occurred>",
  "reasoning": "<free-text causal narrative, 100–500 words>",
  "sops": [
    {
      "id": "<slug, e.g. verify-after-write>",
      "when": "<trigger condition>",
      "what": "<action the agent should take>",
      "why": "<consequence of omission>",
      "source_type": "error" | "success",
      "priority": "critical" | "recommended" | "nice-to-have"
    }
  ],
  "edits": [
    {
      "file": "<target skill file, e.g. SKILL.md>",
      "op": "insert_after" | "replace" | "delete" | "create",
      "target_section": "<heading or line anchor>",
      "content": "<markdown content to insert or replace with>"
    }
  ],
  "new_files": [
    {
      "path": "references/<filename>.md",
      "content": "<full file content>"
    }
  ]
}
```

### 4.1 Validation Rules (Programmatic Guardrails)

These are enforced automatically. A patch that violates any rule is rejected.

1. **Referential integrity.** Every `edit.file` must name a file that exists in the target skill directory or is created by a `new_files` entry in the same patch.
2. **No overlapping edits.** Two edits in the same patch MUST NOT target overlapping line ranges within the same file.
3. **Atomic link pairs.** If an edit inserts a cross-reference link to a `references/*.md` file, that file must exist or be created in `new_files` within the same patch. Drop both if either is missing.
4. **SoP non-duplication.** Each `sop.id` must be unique within the patch.
5. **Content length.** No single `edit.content` block may exceed 2000 tokens. If more space is needed, split into a SKILL.md summary and a `references/` deep-dive.
6. **No task-specific literals.** Content must not contain file paths, variable names, or string literals copied verbatim from the trace unless they illustrate a general pattern in a clearly marked example block.

## 5. Merge / Consolidation Protocol

> This section governs how multiple patches are combined into a single coherent skill update. It is used by the Merge Operator agent.

### 5.1 Hierarchical Merge Procedure

Given a pool `P` of `N` patches:

1. **Partition** `P` into groups of up to `B_merge` patches (default: 32).
2. **For each group**, a merge call produces one consolidated patch by:
   a. Deduplicating SoPs with identical or near-identical `when`/`what` pairs. Keep the version with the strongest justification or synthesize a superior version.
   b. Resolving conflicts: if two SoPs prescribe contradictory actions for overlapping trigger conditions, prefer the one with higher confidence and more supporting traces. If tied, synthesize a conditional rule.
   c. Preserving unique insights: every SoP that addresses a distinct failure or success mode must survive unless it is task-specific noise.
3. **Recurse** until a single consolidated patch remains (at most `ceil(log_{B_merge}(N))` levels).

### 5.2 Prevalence-Weighted Survival

During each merge step, count how many input patches independently proposed each SoP theme. The merge operator MUST:

- **Elevate** SoPs cited by ≥ 3 independent patches to `priority: critical` and place them in the main `SKILL.md`.
- **Retain** SoPs cited by 2 patches at `priority: recommended`, placed in `SKILL.md` under a secondary section.
- **Route** SoPs cited by only 1 patch to `references/` as edge-case guidance, unless the analyst confidence is `high` and the failure mode is catastrophic, in which case promote to `recommended`.
- **Discard** `ambiguous`-outcome SoPs that lack corroboration from any non-ambiguous trace.

### 5.3 Conflict Resolution Priority Order

When two SoPs conflict:

1. Validated error patches (`confidence: high`, `analyst_type: error`) win.
2. Unvalidated error patches (`confidence: medium`) next.
3. Success patches next.
4. Ambiguous-outcome patches last.

Within the same tier, the SoP with more independent supporting patches wins.

### 5.4 Post-Merge Validation

After the final merge:

1. Run all §4.1 guardrails against the consolidated patch.
2. Verify that the resulting skill document, after patch application, is valid markdown with no broken internal links.
3. Confirm total skill length does not exceed a configurable token budget (default: 8000 tokens for `SKILL.md`; unlimited for `references/`).

## 6. Target Skill Scaffold

If no existing target skill is provided, initialize with this empty scaffold before applying patches:

```markdown
# [Domain] Agent Skill
## Overview
<!-- Auto-generated. Describe the task domain. -->
## Critical Rules
<!-- SoPs with priority: critical go here. -->
## Recommended Practices
<!-- SoPs with priority: recommended go here. -->
## Common Failure Modes
<!-- Error-derived SoPs organized by root_cause_label. -->
## Effective Patterns
<!-- Success-derived SoPs. -->
## References
<!-- Links to references/*.md files for edge cases. -->
```

## 7. Session-Source-Specific Guidance

### 7.1 `.claude` Sessions

- Tool calls appear under `tool_use` blocks with `name` and `input` fields. The tool result follows in a `tool_result` block. Map these to the canonical `tool_calls` / `tool_output` schema.
- Claude sessions may include `thinking` blocks (extended thinking). Treat these as part of the reasoning trace for analysis but do not quote them verbatim in patches because they may contain sensitive intermediate reasoning.
- Multi-tool turns: Claude may issue multiple tool calls in a single assistant turn. Analyze each call independently but note the ordering, as ordering errors are a known failure mode.

### 7.2 `.codex` Sessions

- Codex CLI sessions serialize tool calls as `function_call` objects with `name` and `arguments`. Map `name` to the canonical tool name and parse `arguments` as JSON.
- Codex often operates in a sandboxed environment with network restrictions. If a trace shows a network-related failure, classify under `environment-mismatch` and note the sandbox constraint in the SoP.
- Approval-gated commands: Codex may pause for user approval before executing certain commands. The trace will show an approval event. Factor this into phase segmentation — the pause is not idle time but a human-in-the-loop checkpoint.

### 7.3 Normalizing Across Sources

When analyzing a mixed pool of `.claude` and `.codex` traces, the merge operator must treat source-specific tool names as equivalent where they perform the same function (for example, `bash` / `shell` / `terminal` are all shell execution; `write_file` / `create_file` / `edit_file` are all file-write operations). SoPs should reference the *action category*, not the platform-specific tool name.

## 8. Operational Constraints

- **No parameter updates.** The analyst and merge agents operate with frozen weights. All improvements are expressed as skill-document edits.
- **No external retrieval at inference.** The evolved skill must be self-contained. Do not produce patches that assume a retrieval module will be available at runtime.
- **Deterministic reproducibility.** Given the same trace pool and the same random seed, the pipeline should produce the same consolidated patch. Avoid non-deterministic tie-breaking in merge logic.
- **Token budget awareness.** The analyst must be conscious that the target skill will be prepended to an agent's system prompt. Overly verbose skills waste context window capacity. Prefer concise, high-signal rules.

## 9. Bundled Resources

- `templates/error_analyst_system.md` for failure-trace analyst prompts.
- `templates/success_analyst_system.md` for reusable success-pattern extraction.
- `templates/merge_operator_system.md` for consolidation across multiple analyst patches.
- `templates/metadata_envelope.json` as the canonical metadata scaffold.
- `scripts/validate_patch.py` to enforce the §4.1 guardrails.
- `scripts/apply_patch.py` to turn a Trace2Skill patch into a unified diff preview or write the change set to disk.
