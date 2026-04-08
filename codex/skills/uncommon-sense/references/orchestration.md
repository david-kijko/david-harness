# Uncommon Sense Orchestration Reference

Use this reference when you need the full phase model, artifact shapes, or component traceability.

The prose model in this file is backed by executable resources in `scripts/`:

- `scripts/uncommon_sense.py` implements intent compilation, task ledgers, evidence merge, synthesis, quality scoring, telemetry, and an end-to-end scaffold.
- `scripts/run_pipeline.sh` is a thin shell wrapper around the Python pipeline command.
- `scripts/render_artifact.sh` renders Markdown artifacts to `html`, `pdf`, or `docx` through `pandoc` when available.

## Component Model

This skill is built around seven components:

1. Intent compiler
2. Research orchestrator
3. Task ledger
4. Source-tiered evidence layer
5. Synthesis engine
6. Artifact builder
7. Telemetry layer

These components came from the user's provided design brief. The original CSV file was not available in the local filesystem during installation, so this reference captures the supplied component list and requirements directly.

## Phase Model

### Phase 1: Intent Compiler

Goal: turn a vague or sprawling request into an operational brief.

Recommended sequence:

1. Literal parse of explicit nouns, verbs, named entities, constraints, and requested outputs.
2. Latent requirement extraction:
   - what else must be true for usefulness
   - what expert-grade deliverables are implied
   - what quality bar is silently expected
3. Completion criteria matrix:
   - requirement
   - evidence needed
   - done-when predicate
4. Complexity scoring across:
   - ambiguity
   - domain breadth
   - expertise depth
   - evidence difficulty
   - artifact complexity

Suggested execution modes:

- total under 8: single-agent fast path
- 8 to 14: selective parallel mode
- 15 or more: full swarm

Codex mapping:

- single-agent -> stay in the lead session
- selective parallel -> delegate only when the user has explicitly asked for or clearly authorized delegated work
- full swarm -> reserve for cases where delegation is clearly authorized and the lanes are independent

Suggested artifact:

```json
{
  "intent_contract": {
    "explicit_requirements": [],
    "latent_requirements": [],
    "evidence_targets": [],
    "completion_criteria": [],
    "complexity_score": 0,
    "selected_superpowers": [],
    "authority_sources_needed": [],
    "artifact_targets": []
  }
}
```

Implementation:

```bash
python3 ~/.codex/skills/uncommon-sense/scripts/uncommon_sense.py intent-compile \
  --query "Investigate our telemetry stack and propose a remediation plan"
```

### Phase 2: Plan And Task Ledger

Goal: convert the intent contract into durable execution state.

Each task should contain:

- `id`
- `description`
- `assigned_superpower`
- `swarm_lane`
- `status`
- `depends_on`
- `evidence_slot`
- `authority_tier`

Suggested artifact:

```json
{
  "task_ledger": [
    {
      "id": "T-001",
      "description": "Investigate authoritative pricing sources",
      "assigned_superpower": "exa",
      "swarm_lane": "A",
      "status": "pending",
      "depends_on": [],
      "evidence_slot": null,
      "authority_tier": "primary"
    }
  ]
}
```

Implementation:

```bash
python3 ~/.codex/skills/uncommon-sense/scripts/uncommon_sense.py create-ledger \
  --intent-contract /path/to/intent_contract.json
```

### Phase 3: Swarm Orchestrator

Goal: fan out work in parallel, then fan it back in.

Fan-out guidance:

- give each worker a narrow, concrete assignment
- keep write scopes disjoint when code changes are involved
- ask workers to return evidence, gaps, and confidence
- keep the lead responsible for synthesis and for deciding whether delegation is warranted at all

Evidence policy:

- Tier 1: primary or authoritative
- Tier 2: strong secondary
- Tier 3: reconnaissance

A requirement should not be considered satisfied by Tier 3 alone if a stronger source is reasonably available.

Fan-in guidance:

- merge evidence by requirement, not by lane
- deduplicate URLs and repeated claims
- note unmet criteria immediately

Suggested artifact:

```json
{
  "synthesis_state": {
    "evidence_by_requirement": {
      "REQ-001": {
        "evidence": [],
        "tier": 1,
        "confidence": 0.92
      }
    },
    "unmet_criteria": [],
    "coverage_score": 0.0
  }
}
```

Implementation:

```bash
python3 ~/.codex/skills/uncommon-sense/scripts/uncommon_sense.py merge-evidence \
  --intent-contract /path/to/intent_contract.json \
  --task-ledger /path/to/task_ledger.json \
  --evidence-dir /path/to/evidence
```

Expected evidence record shape:

```json
{
  "requirement_id": "EXP-001",
  "title": "Official pricing page",
  "source": "https://example.com/pricing",
  "tier": "primary",
  "confidence": 0.92,
  "summary": "Pricing details pulled from the first-party site."
}
```

### Phase 4: Synthesis Engine And Artifact Builder

Goal: decide when there is enough signal, then build the deliverable.

Suggested rules:

- compute `coverage_score = met_criteria / total_criteria`
- if `coverage_score < 0.85`, generate gap-fill work before building
- build around user intent, not raw chronology
- preserve citation integrity for research outputs
- ensure code outputs include verification where possible

Suggested artifact:

```json
{
  "final_artifact": "...",
  "artifact_metadata": {
    "format": "markdown",
    "sections": [],
    "citation_map": {},
    "render_targets_available": ["md", "html", "pdf", "docx", "json"]
  }
}
```

Implementation:

```bash
python3 ~/.codex/skills/uncommon-sense/scripts/uncommon_sense.py build-artifact \
  --intent-contract /path/to/intent_contract.json \
  --synthesis-state /path/to/synthesis_state.json \
  --format markdown \
  --output /path/to/final_artifact.md

~/.codex/skills/uncommon-sense/scripts/render_artifact.sh \
  /path/to/final_artifact.md \
  /path/to/final_artifact.pdf
```

### Phase 5: Quality Gate

Goal: confirm the result meets or exceeds explicit and latent intent.

Criterion scoring:

- `0` not addressed
- `1` partially addressed
- `2` fully met
- `3` exceeded

Formula:

`intent_fidelity_score = sum(scores) / (total_criteria * 3) * 100`

Decision policy:

- `>= 85%`: pass
- `60-84%`: targeted remediation loop
- `< 60%` or loops exhausted: escalate to `exa`

Use the installed `exa` skill as the operational fallback corresponding to the user's requested "exa 360" capability. Pass:

- the original query
- the current intent contract
- unmet criteria
- current synthesis state

Then merge the new evidence, rebuild, and re-evaluate.

Implementation:

```bash
python3 ~/.codex/skills/uncommon-sense/scripts/uncommon_sense.py quality-gate \
  --intent-contract /path/to/intent_contract.json \
  --synthesis-state /path/to/synthesis_state.json \
  --artifact /path/to/final_artifact.md
```

## Telemetry Expectations

Capture enough detail to explain how the result was produced:

- final intent contract
- task ledger with statuses
- source provenance chain
- superpowers or skills invoked
- timestamps or phase order
- quality gate outcome

Telemetry is for traceability and synthesis integrity. Do not overwhelm the user with it unless it materially helps.

Implementation:

```bash
python3 ~/.codex/skills/uncommon-sense/scripts/uncommon_sense.py telemetry-snapshot \
  --intent-contract /path/to/intent_contract.json \
  --task-ledger /path/to/task_ledger.json \
  --synthesis-state /path/to/synthesis_state.json \
  --artifact-metadata /path/to/final_artifact.metadata.json \
  --quality-report /path/to/quality_report.json
```

## Superpower Selection Heuristics

Choose a specialist skill when it clearly improves results:

- `exa`: live-web research, recent facts, citations, source expansion
- `openai-docs`: official OpenAI docs and model guidance
- `conductor`: structured workflow artifacts in `conductor/`
- `superconductor`: supervised spec-to-execution pipeline
- native Codex tooling: repo inspection, code changes, tests, shell execution

If a named skill is unavailable in the current session, continue with the best native fallback and say so briefly.

## Traceability Map

The seven requested components map to this skill as follows:

- Intent Compiler -> Phase 1 intent contract and latent-requirement extraction
- Research Orchestrator -> Phase 3 swarm fan-out and fan-in
- Task Ledger -> Phase 2 durable task objects and status tracking
- Source-Tiered Evidence Layer -> Phase 3 evidence ranking and authority policy
- Synthesis Engine -> Phase 4 coverage-aware synthesis state
- Artifact Builder -> Phase 4 deliverable construction
- Telemetry Layer -> telemetry expectations and provenance capture

## One-Shot Scaffold

For a single end-to-end scaffold run:

```bash
~/.codex/skills/uncommon-sense/scripts/run_pipeline.sh \
  --query "Map the AIQ architecture gaps and propose an implementation plan" \
  --workspace /tmp/uncommon-sense-runs
```

This creates a run directory with:

- `query.txt`
- `component_blueprints.json`
- `intent_contract.json`
- `task_ledger.json`
- `synthesis_state.json`
- `artifacts/final_artifact.md`
- `artifacts/final_artifact.metadata.json`
- `quality_report.json`
- `telemetry.json`
- `manifest.json`

## Claude Agent Teams Notes

Current Claude docs say:

- agent teams are experimental and must be enabled with `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
- they are best for independent parallel work
- they preserve separate context windows per teammate
- they use more total tokens than subagents or a single session

This skill therefore uses agent teams to protect the lead context window during fan-out, then returns to the lead for synthesis and quality control.
