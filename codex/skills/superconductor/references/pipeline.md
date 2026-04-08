# Superconductor Pipeline — Detailed Protocol Reference

Read this file when executing `/conductor:superconductor`. This is the deterministic protocol that every run follows.

## Preferred Execution: Superconductor CLI

The recommended way to run superconductor is via the unified CLI, which controls the outer loop from Node.js and drives the agent via the codex app-server WebSocket protocol. This prevents the agent from declaring partial completion.

```bash
# Full run (setup + execution):
superconductor run <repo-root> --spec <requirements-source>

# Resume existing run:
superconductor resume <repo-root>

# Check status:
superconductor status <repo-root>

# Gate check only:
superconductor gate <repo-root>
```

The CLI handles: state detection, track batching, turn dispatch, gate checking, and loop control. The agent only executes each wave assignment.

## Core Invariants

1. **Never stop at a proof slice.** The pipeline runs until the requirements matrix is exhausted.
2. **Artifacts are the memory.** Each invocation resumes from `requirements-matrix.json`. No rediscovery.
3. **Same loop every time.** No improvisation, no chatty replanning. The 9 stages execute in order.
4. **The CLI controls the loop.** The agent does not decide when to stop. The superconductor CLI runs the gate check after every wave and only exits on gate pass.
5. **Workers are not explorers.** Workers implement. Investigation happens in Stages 1-7 only (setup phase).

## Resume Protocol

When `/conductor:superconductor` is invoked:

1. Check for existing `conductor/superconductor/*/requirements-matrix.json` files.
2. If a matrix exists with incomplete requirements:
   - Read the matrix
   - Identify the current stage from `sufficiency-report.json`
   - Resume from that stage
   - Announce: "Resuming superconductor run `<run-id>` at Stage X. Y of Z requirements remain."
3. If no matrix exists: start fresh from Stage 1.
4. If a matrix exists with all requirements verified: announce completion, offer to start a new run.

## Stage Details

### Stage 1: Intake

**Input:** A requirements source (file path, track ID, plain text, or URL).

**Process:**
1. Parse the requirements source into atomic, numbered requirements.
   - For `.docx`: extract text and parse sections into requirements.
   - For `.md`/`.txt`: parse headings and bullet points as requirements.
   - For plain text: decompose the prompt into explicit statements.
2. Each requirement gets: `id`, `text`, `domain`, `status: "pending"`, `track_id: null`, `claims: []`.
3. Domain classification uses these categories:
   - `backend` — server logic, APIs, database, business rules
   - `frontend` — UI components, pages, routing, rendering
   - `docs` — documentation pages, content, word counts
   - `infra` — deployment, CI/CD, Docker, monitoring
   - `testing` — test suites, coverage, E2E tests
   - `ux` — search, navigation, TOC, breadcrumbs, accessibility
   - `api` — API documentation, endpoint reference, SDKs
   - `pipeline` — automation, webhooks, file watchers, CodeGraph loops
   - `security` — auth, secrets, access control
   - `data` — data models, migrations, schema changes
4. Create the run folder and scaffold templates.

**Output:** `requirements-matrix.json` with all requirements parsed and classified.

### Stage 2: Intent Alignment

**Input:** `requirements-matrix.json` + harness docs.

**Process:**
1. For each requirement, generate 1+ explicit claims.
   - A claim is a testable statement: "The system SHALL [do X]" or "The docs SHALL [contain Y]".
2. Compare each claim against harness docs:
   - Search `product.md`, `tech-stack.md`, `workflow.md` for confirming or contradicting evidence.
   - Search existing code for implementation evidence.
3. Classify: `confirmed`, `contradicted`, `underdocumented`, `unimplemented`.
4. Write gaps to `docs-gap-report.md`.

**Output:** `intent-alignment-report.md` with full claim table. `requirements-matrix.json` updated with claim mappings.

### Stage 3: CGC Investigation

**Input:** Claim table from Stage 2.

**Process:**
1. If CGC MCP is available:
   - Query the code graph for each unimplemented/underdocumented claim.
   - Suppress utility nodes (loggers, config loaders, etc.) to focus on domain logic.
   - Look for: missing edges, orphaned modules, bridge nodes, ownership gaps, boundary fragility.
2. If CGC MCP is unavailable:
   - Use `Glob` to map the file tree.
   - Use `Grep` to search for claim-related symbols.
   - Use `Read` to inspect key files.
   - Document: "CGC unavailable. Investigation performed via file system analysis."
3. Generate questions for unresolved claims.

**Output:** `question-pack.json` updated with investigation questions.

### Stage 4: Closure

**Input:** `question-pack.json` + code evidence from Stage 3.

**Process:**
1. Use sequential-thinking to order questions by impact and dependency.
2. Resolve questions in order:
   - Read code files to answer code questions.
   - Check docs to answer doc questions.
   - Mark questions as `resolved` or `blocked`.
3. Build NLM harness dump if NotebookLM is available.
4. Build research notebook for remaining contradictions.

**Output:** `question-pack.json` with resolution status. `dependency-closure.json` updated.

### Stage 5: Sufficiency Gate

**Input:** All artifacts from Stages 1-4.

**Process:**
1. Run triple gut check:
   - Prompt: Does the current work still match user intent?
   - CGC: Does claim-to-code mapping still hold?
   - NLM: Are harness dumps current?
2. Count high-impact claims by status.
3. Decision:
   - If >0 unresolved high-impact claims: **LOOP BACK TO STAGE 3** with the specific unresolved claims.
   - If all high-impact claims resolved: **PROCEED TO STAGE 6**.
   - Maximum loops: 3. After 3 loops, halt and report remaining gaps to user.

**Output:** `sufficiency-report.json` with pass/fail and blocking reasons.

### Stage 6: Requirements Matrix Decomposition

**Input:** `requirements-matrix.json` with all claims resolved.

**Process:**
1. Group requirements by domain.
2. For each domain group with 1+ requirements:
   - Generate a track ID: `<domain>_<YYYYMMDD>`
   - Assign all requirements in the group to this track.
   - Set requirement status to `in-track`.
3. Verify exhaustion: `SELECT * FROM requirements WHERE status = 'pending'` must return 0 rows.
4. If any pending: create a catch-all track or ask user to clarify.

**Output:** `requirements-matrix.json` fully mapped. `superconductor.md` with track manifest.

### Stage 7: Track Generation

**Input:** Track manifest from Stage 6.

**Process:**
For each track:
1. Create directory: `conductor/tracks/<track_id>/`
2. Generate `spec.md`:
   - Overview: what this track accomplishes
   - Functional Requirements: one FR per requirement in the group
   - Non-Functional Requirements: inferred from domain and project workflow
   - Acceptance Criteria: derived from each requirement's claims
   - Out of Scope: explicitly list what adjacent domains handle
3. Generate `plan.md`:
   - Phase 1: Setup and scaffolding
   - Phase 2+: Implementation tasks grouped logically
   - Final Phase: Testing and verification
   - Every phase gets a completion verification task
4. Write `metadata.json`, `index.md`.
5. Register in `conductor/tracks.md`.
6. If plan has parallelizable tasks: invoke `scrum` for wave optimization.

**Output:** All track directories populated. `conductor/tracks.md` updated.

### Stage 8: Worker Fan-Out

**Input:** All generated tracks.

**Process:**
1. Read `worker-context-manifest.json` for skill requirements.
2. Determine execution order:
   - If scrum wave files exist: follow wave order.
   - If no scrum output: execute tracks sequentially by dependency.
3. For each track:
   a. Run pre-spawn checklist (6 items — see SKILL.md Stage 8).
   b. Spawn worker with:
      - Track spec + plan
      - Relevant harness docs
      - Required skills
      - Workflow instructions
      - Explicit "complete all tasks" directive
   c. Monitor progress via plan.md task markers.
   d. On worker completion: update requirements-matrix.json.
4. For parallel-eligible tracks:
   - Spawn up to N workers concurrently (N from scrum context budget or default 3).
   - Wait for all to complete before moving to next wave.

**Output:** Code changes committed. `requirements-matrix.json` updated with `implemented` status.

### Stage 9: Completion Gate

**Input:** `requirements-matrix.json`.

**Process:**
1. Tally: `pending`, `in-track`, `implemented`, `verified`.
2. If `in-track` > 0: return to Stage 8.
3. If `implemented` > 0: trigger review, then mark `verified`.
4. If all `verified`: render completion summary, update sufficiency to complete.
5. If context is running low: save state and announce pause point.

**Output:** Final `superconductor.md` with completion status.

## Worker Spawn Template

Every worker receives this context envelope:

```
## Worker Assignment: <track_id>

### Your Task
Complete ALL tasks in the implementation plan below. Do not stop at a proof slice.

### Pre-Spawn Verification (Completed)
- [x] Prompt gut check: <restated claims>
- [x] CGC gut check: <mapping status>
- [x] NLM gut check: <harness dump status>
- [x] Sequential-thinking: <closure order>
- [x] Skills loaded: <skill list>
- [x] Exa: <needed/not-needed>

### Required Skills
<list from worker-context-manifest.json>

### Spec
<contents of spec.md>

### Plan
<contents of plan.md>

### Workflow
Follow the Task Workflow from workflow.md:
1. Mark task in-progress
2. Write failing tests (Red)
3. Implement to pass (Green)
4. Refactor
5. Verify coverage
6. Commit with conventional message
7. Attach git note
8. Update plan.md with commit SHA
9. Commit plan update

### Harness Context
<relevant subset of harness docs for this track's domain>

### Completion Criteria
Every task in the plan must be marked [x] with a commit SHA.
Every phase must have a checkpoint.
Do not declare done until the full plan is executed.
```

## Error Recovery

| Error | Recovery |
|---|---|
| Worker fails mid-track | Save progress to plan.md, re-spawn worker from next pending task |
| CGC MCP unavailable | Fall back to file system analysis, document the gap |
| NLM unavailable | Skip NLM gut check, document the gap, rely on prompt + CGC checks |
| Context budget exceeded | Save requirements-matrix.json, announce pause point with stage number |
| Requirements source ambiguous | Halt at Stage 1, ask user to clarify specific requirements |
| Circular track dependencies | Flag in superconductor.md, ask user to break the cycle |
| Maximum Stage 3-5 loops reached | Halt with remaining gaps, ask user for guidance |
