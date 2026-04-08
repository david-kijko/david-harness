---
name: crispy
description: Use when a task is large, ambiguous, or likely to turn into a mega-prompt and you need a disciplined QRSPI workflow with constrained sub-agents, grounded research, vertical planning, and proof-before-completion.
---

# Crispy

Crispy is the QRSPI protocol for Codex on this machine:

1. **Questions** — deconstruct intent into missing facts and decisions.
2. **Research** — gather objective repo/system/web truth with blind or bounded research lanes.
3. **Structure Outline** — define the architecture and touched boundaries without implementation.
4. **Plan** — break work into vertical slices with verification per slice.
5. **Implement** — execute with proof, not vibes.

Crispy exists to prevent the **mega-prompt fallacy**: once a task is broad enough that one prompt would mix intent, repo discovery, design, implementation, and verification, split it into phases instead of asking one agent to “just do it”.

## Use This Skill When

Use Crispy when one or more are true:
- the task spans multiple subsystems, repos, tools, or environments
- the user gives a high-level outcome rather than a step-by-step request
- the work needs research, architecture, planning, and implementation in one effort
- you are at risk of exceeding a sane instruction budget in one prompt
- correctness matters enough that you need explicit proof artifacts or verification gates

Do **not** use Crispy for a tiny one-step task that can be completed directly.

## Core Rules

1. **Never jump from vague intent straight to code.**
2. **Keep instruction budgets low.** If a lane would need more than ~40 substantive instructions, split it again.
3. **Do objective research before declaring root cause.**
4. **Prefer vertical slices** over horizontal subsystem-by-subsystem implementation.
5. **No completion claims without fresh evidence.**
6. **After any pushed commit or workflow-triggering change, inspect actual GitHub Actions logs**, not the summary card.
7. **For auth/container/env/deployment diagnosis, do not claim root cause until you have completed this sequence:**
   - inspect host auth files
   - inspect container auth files
   - inspect the app’s actual detection logic
   - only then state root cause

## Artifact Contract

Crispy uses these lightweight artifacts/concepts:

- `QUESTION_LIST.md` — what still must be learned
- `OBJECTIVE_CONTEXT.md` — grounded facts only
- `STRUCTURE_OUTLINE.md` — architecture, boundaries, and logic flow without implementation
- `EXECUTION_PLAN.md` — vertical slices, verification, and rollout order

These do not all need to be persisted as files for every task, but the concepts must be present.

## Phase 1 — Questions

Goal: translate intent into a bounded investigation set.

Output shape:
- current state questions
- affected boundaries
- data/auth/runtime assumptions to verify
- decisions that are preferences vs discoverable facts

If the task is feature work, invoke **`brainstorming`** first.
If the task is vague or orchestration-heavy, invoke **`uncommon-sense`** first.

Questioner rules:
- do not propose code
- do not hallucinate repo structure
- separate **discoverable facts** from **preference decisions**
- if the user already supplied a plan, compress questions to only the unresolved edges

## Phase 2 — Research

Goal: gather truth without leaking too much implementation bias into the research lane.

Use:
- local repo/system inspection first
- **`exa`** for live web research, official docs, or current external facts
- `dispatching-parallel-agents` or `subagent-driven-development` when independent research lanes are warranted

Research rules:
- prefer blind or bounded research prompts when the end-state intent would bias findings
- record facts, file anchors, commands, and sources
- label hypotheses as hypotheses
- for auth/env/deployment incidents, obey the required root-cause sequence before making a root-cause claim

Output shape:
- exact files / symbols / docs / commands checked
- verified facts
- open gaps
- explicit risks and unknowns

## Phase 3 — Structure Outline

Goal: define the implementation shape before editing.

Use **`writing-plans`** once the architecture is stable enough to plan.

Structure outline should include:
- touched subsystems
- interface / API / data model changes
- lifecycle or control-flow changes
- error handling and rollback expectations
- what will be verified and how

Do **not** write full implementation in this phase.

## Phase 4 — Plan

Goal: create vertical, testable slices.

Every slice must include:
- implementation target
- verification target
- blast-radius note
- dependency ordering

Default slice pattern:
1. smallest enabling backend/control-plane change
2. one end-to-end vertical path
3. hardening / edge cases
4. observability / docs / rollout follow-up

Prefer:
- one vertical feature slice that can be proven
- then the next

Avoid:
- “do all DB changes, then all API changes, then all UI changes” with no runnable midpoint

## Phase 5 — Implement + Verify

Use the smallest relevant execution skills:
- **`systematic-debugging`** for bugs or regressions
- **`verification-before-completion`** before claiming success
- **`proofshot`** for UI verification
- **`dispatching-parallel-agents`** or **`subagent-driven-development`** when write scopes are safely separable
- **`writing-skills`** when creating or editing skills

Implementation rules:
- preserve what already works
- minimize blast radius
- verify each slice before proceeding
- if workflows are triggered, inspect the real failed step logs before saying the work is done

## Recommended Routing Table

| Need | Route |
|---|---|
| vague high-level task | `uncommon-sense` |
| new feature / behavior design | `brainstorming` |
| multi-step implementation design | `writing-plans` |
| web/current documentation | `exa` |
| bug investigation | `systematic-debugging` |
| parallel independent lanes | `dispatching-parallel-agents` |
| implementation with isolated tasks | `subagent-driven-development` |
| UI proof | `proofshot` |
| pre-completion honesty gate | `verification-before-completion` |
| creating or editing a skill | `writing-skills` |

## Minimal Operating Pattern

1. Restate goal in one sentence.
2. Decide whether the task needs Crispy.
3. Build the implicit `QUESTION_LIST`.
4. Research locally first; use `exa` when the facts are external or current.
5. Produce a `STRUCTURE_OUTLINE` before code changes.
6. Convert into an `EXECUTION_PLAN` of vertical slices.
7. Implement with the smallest necessary specialist skills.
8. Verify with commands, tests, Proofshot, and workflow logs.
9. Only then claim success.

## Common Failure Modes

- **Mega-prompt collapse**: too many instructions in one shot; split phases.
- **Intent leakage into research**: researchers start recommending what “should” exist instead of finding what does exist.
- **Horizontal slop**: all layers change at once without a provable vertical path.
- **False completion**: claiming “fixed” before tests, proof, or workflow logs.
- **Workflow blindness**: pushing changes and never reading the failing CI step.

## Codex-Specific Notes

- Personal skill location on this machine is `~/.codex/skills/<skill-name>/SKILL.md`.
- After installing or changing a skill, verify it in a **fresh** ephemeral Codex session:
  - `codex exec --skip-git-repo-check --ephemeral ...`
- If a task mentions Crispy explicitly, use this protocol instead of improvising.
