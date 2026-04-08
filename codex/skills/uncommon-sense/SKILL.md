---
name: "uncommon-sense"
description: "Infer hidden requirements and orchestrate complex multi-step work. Use when the user says 'uncommon sense', asks for intent-first planning, wants a vague request turned into an operational brief, or needs research, planning, synthesis, and quality checks coordinated into one artifact."
argument-hint: "[request]"
---

# Uncommon Sense

Use this skill for complex, ambiguous, or multi-artifact work where the user's real success criteria are broader than the literal wording of the prompt.

This skill turns a fuzzy request into an intent contract, routes work to the right capability, fans out parallel execution when useful, and loops on quality before delivery.

## Codex Execution

When this skill is used in Codex:

1. Restate the interpreted request in one sentence.
2. Build the intent contract.
3. Choose the lightest execution mode that can satisfy the request.
4. Use the bundled scripts when persisted artifacts will help.
5. Keep orchestration and synthesis in the lead context.
6. Only delegate parallel work when the user has explicitly asked for it or clearly authorized it.

## Bundled Scripts

Use the bundled scripts to persist orchestration state instead of hand-rolling JSON by memory.

Core CLI:

```bash
python3 ~/.codex/skills/uncommon-sense/scripts/uncommon_sense.py --help
```

Common commands:

```bash
python3 ~/.codex/skills/uncommon-sense/scripts/uncommon_sense.py pipeline \
  --query "Build a competitive analysis of AI coding assistants" \
  --workspace /tmp/uncommon-sense-runs

python3 ~/.codex/skills/uncommon-sense/scripts/uncommon_sense.py intent-compile \
  --query "Investigate our telemetry stack and recommend gaps"

python3 ~/.codex/skills/uncommon-sense/scripts/uncommon_sense.py create-ledger \
  --intent-contract /tmp/uncommon-sense-runs/<run>/intent_contract.json

python3 ~/.codex/skills/uncommon-sense/scripts/uncommon_sense.py merge-evidence \
  --intent-contract /tmp/uncommon-sense-runs/<run>/intent_contract.json \
  --task-ledger /tmp/uncommon-sense-runs/<run>/task_ledger.json \
  --evidence-dir /tmp/uncommon-sense-runs/<run>/evidence

python3 ~/.codex/skills/uncommon-sense/scripts/uncommon_sense.py quality-gate \
  --intent-contract /tmp/uncommon-sense-runs/<run>/intent_contract.json \
  --synthesis-state /tmp/uncommon-sense-runs/<run>/synthesis_state.json \
  --artifact /tmp/uncommon-sense-runs/<run>/artifacts/final_artifact.md
```

Shell helpers:

```bash
~/.codex/skills/uncommon-sense/scripts/run_pipeline.sh \
  --query "Map the AIQ architecture gaps and propose an implementation plan"

~/.codex/skills/uncommon-sense/scripts/render_artifact.sh \
  /tmp/uncommon-sense-runs/<run>/artifacts/final_artifact.md \
  /tmp/uncommon-sense-runs/<run>/artifacts/final_artifact.pdf
```

## When To Use It

Use `uncommon-sense` when one or more of these are true:

- the user asks for "the best approach", "figure out what I really need", "think through this", or an end-to-end outcome rather than a single action
- the request spans multiple domains such as research, planning, coding, writing, or analysis
- latent deliverables are likely required for the answer to feel complete
- the work benefits from parallel agents, multiple research lanes, or structured synthesis
- the user wants a high-confidence artifact with explicit quality checking

Do not use it for a narrow one-step task that can be completed directly without orchestration.

## Operating Rules

1. Build an `intent_contract` before doing substantial work.
2. Treat latent requirements as first-class requirements, not nice-to-haves.
3. Choose the lightest execution mode that can satisfy the intent:
   - low complexity: single-agent fast path
   - medium complexity: selective parallel lanes
   - high complexity: full swarm
4. Prefer the best available specialist skill before inventing a new workflow.
5. Use delegated parallel agents only when the user has asked for or clearly authorized delegated work.
6. Synthesize through the main agent. Worker agents gather, implement, or verify; the orchestrator integrates.
7. Run a quality gate before final delivery.
8. If quality is still below threshold after internal remediation, escalate to the installed `exa` skill as the practical equivalent of "exa 360".
9. Prefer the bundled CLI artifacts and schemas when persisting orchestration state.
10. If running inside Codex, prefer paths rooted at `~/.codex/skills/uncommon-sense/`.

## Workflow

### 1. Intent Compiler

Create a compact `intent_contract` with:

- `explicit_requirements`
- `latent_requirements`
- `evidence_targets`
- `completion_criteria`
- `complexity_score`
- `selected_superpowers`
- `artifact_targets`

Start from the user's literal wording, then ask:

- What else must be true for this to be genuinely useful?
- What would an expert add without being asked?
- What evidence or verification would make the answer trustworthy?

Use the contract to define done-when predicates, not just a topic summary.

### 2. Superpower Selection

Select the best specialist skill or native capability for each requirement cluster.

Suggested routing:

- live web research, freshness, citations, market scans, source gathering: `exa`
- official OpenAI product and API guidance: `openai-docs`
- conductor workflow setup or management: `conductor`
- autonomous spec-to-execution pipeline: `superconductor`
- local code investigation, editing, testing, or shell work: native Codex tools

If multiple options fit, prefer the most authoritative and least expensive path.

### 3. Task Ledger

Translate the contract into a durable task ledger:

- one task per requirement or tightly related requirement cluster
- owner or assigned capability
- dependency edges
- evidence slot
- status: `pending`, `in_progress`, `complete`, `partial`, or `blocked`

Keep the ledger visible in plan updates when the task is large enough to benefit from progress tracking.

### 4. Swarm Orchestration

When parallel execution is justified, split the work into independent lanes and assign each lane a clear ownership boundary.

In Codex:

- keep the lead session responsible for task assignment, synthesis, and quality gating
- keep delegated lanes scoped to research, implementation, or verification
- only fan out when delegation is explicitly allowed for the task at hand

Worker lanes should:

- gather evidence, implement code, or produce draft artifacts
- record source quality and open gaps
- avoid overlapping write scopes unless coordination is required

The orchestrator should:

- merge lane outputs into shared synthesis state
- deduplicate overlapping findings
- detect unmet criteria early

### 5. Evidence Tiers

Rank evidence while work is happening:

- Tier 1: primary or authoritative sources such as official docs, APIs, specs, first-party statements
- Tier 2: strong secondary sources such as peer-reviewed work or reputable analysis
- Tier 3: reconnaissance such as forums, blogs, or anecdotal reports

Do not mark a criterion satisfied with only Tier 3 evidence when a stronger tier is reasonably available.

### 6. Synthesis And Artifact Build

Build the final artifact around the intent contract, not around the order work was performed.

Possible artifact forms:

- decision memo or report
- implementation patch plus tests
- research brief with citations
- comparison matrix
- structured JSON or CSV
- mixed deliverable with narrative, code, and tables

The final artifact should unify:

- what the user asked
- what the user actually needed
- what evidence supports the output
- what remains uncertain

### 7. Quality Loop

Score each completion criterion on a 0-3 scale:

- `0`: not addressed
- `1`: partially addressed
- `2`: fully met
- `3`: exceeded

Compute an `intent_fidelity_score`.

Default thresholds:

- `>= 85%`: pass and deliver
- `60-84%`: loop once or twice with targeted remediation
- `< 60%` or remediation exhausted: escalate to `exa` for deeper research, merge findings, rebuild, and re-evaluate

Always be transparent about remaining gaps if best-effort delivery is necessary.

## Output Contract

When this skill is active, structure the work so the user can understand:

- the interpreted goal
- the plan or ledger
- what capabilities or skills were selected
- the artifact itself
- the quality outcome and any unresolved risk

Keep the user-facing response concise. The orchestration can be sophisticated without dumping internal scaffolding unless it helps the user.

## Reference Material

For the detailed phase model, artifact schemas, telemetry expectations, and the seven-component traceability map, read [references/orchestration.md](references/orchestration.md).

For executable implementations of the phase model, use:

- [scripts/uncommon_sense.py](scripts/uncommon_sense.py)
- [scripts/run_pipeline.sh](scripts/run_pipeline.sh)
- [scripts/render_artifact.sh](scripts/render_artifact.sh)

For delegated team-brief generation, use:

- [scripts/uncommon_sense.py](scripts/uncommon_sense.py) with `agent-team-brief`
