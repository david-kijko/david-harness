---
name: conductor
description: Use when the user asks Claude to set up conductor, run the superconductor pipeline, create or implement tracks, review completed work, or manage workflow artifacts in conductor/. In Claude's slash-command surface, use /conductor-setup, /conductor-superconductor, /conductor-newTrack, /conductor-implement, /conductor-status, and /conductor-revert.
invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Task
  - TodoWrite
  - AskUserQuestion
---

# Conductor - Context-Driven Development Framework

**Measure twice, code once.**

Conductor transforms your agent into a proactive project manager that follows a strict protocol to **specify, plan, and implement** software features and bug fixes.

In Claude Code, the slash-command surface uses hyphenated names such as `/conductor-setup` and `/conductor-superconductor`. Some protocol sections below retain the original colon labels because they were shared from the Codex bundle.

## Philosophy

Control your code. By treating **context as a managed artifact** alongside your code, you transform your repository into a single source of truth that drives every agent interaction with deep, persistent project awareness.

**Lifecycle:** Intent Alignment -> Context -> Spec & Plan -> Implement -> Review

---

## Trigger Patterns

Use this skill when:
- User runs `/conductor:setup` - Initialize project with Conductor methodology
- User runs `/conductor:superconductor` - Run deterministic brownfield pipeline from requirements to implementation
- User runs `/conductor:newTrack` or `/conductor:track` - Create a new feature/bug track
- User runs `/conductor:implement` or `/conductor:impl` - Execute tasks from plans
- User runs `/conductor:review` - Review completed work against guidelines and the plan
- User runs `/conductor:status` - Show project progress overview
- User runs `/conductor:revert` - Git-aware revert of work
- User asks to "set up conductor" or "use conductor"

---

## Quick Command Reference

| Command | Description |
|---------|-------------|
| `/conductor:setup` | Initialize project (run once per project) |
| `/conductor:superconductor` | Autonomous execution via **superconductor** skill + CLI |
| `/conductor:newTrack [description]` | Create new feature/bug track |
| `/conductor:implement [track]` | Execute tasks from plan |
| `/conductor:review [scope]` | Review work against guidelines and plan |
| `/conductor:status` | Show progress overview |
| `/conductor:revert [target]` | Git-aware revert |

---

## Artifacts Directory Structure

```
conductor/
├── index.md                # Master index linking all project files
├── product.md              # Product vision, users, goals
├── product-guidelines.md   # Brand, voice, style guidelines
├── tech-stack.md           # Technology choices
├── workflow.md             # Development workflow (TDD, commits, etc.)
├── code_styleguides/       # Language-specific style guides
├── tracks.md               # Tracks registry (master list of all tracks)
├── superconductor/         # Brownfield intent-alignment runs and rendered artifacts
│   └── <run-id>/
│       ├── superconductor.md
│       ├── intent-alignment-report.md
│       ├── docs-gap-report.md
│       ├── question-pack.json
│       ├── dependency-closure.json
│       ├── sufficiency-report.json
│       ├── worker-context-manifest.json
│       └── requirements-matrix.json   # THE exhaustive decomposition
├── archive/                # Archived completed tracks
└── tracks/
    └── <track_id>/
        ├── index.md        # Track-level index linking spec, plan, metadata
        ├── metadata.json   # Track metadata
        ├── spec.md         # Detailed specification
        └── plan.md         # Phased implementation plan
```

---

## Universal File Resolution Protocol

**PROTOCOL: How to locate files.**
To find a file (e.g., "Product Definition") within a specific context (Project Root or a specific Track):

1. **Identify Index:** Determine the relevant index file:
   - **Project Context:** `conductor/index.md`
   - **Track Context:**
     a. Resolve and read the **Tracks Registry** (via Project Context).
     b. Find the entry for the specific `<track_id>`.
     c. Follow the link to locate the track's folder. The index is `<track_folder>/index.md`.
     d. **Fallback:** If the track is not yet registered, the index is `conductor/tracks/<track_id>/index.md`.

2. **Check Index:** Read the index file and look for a link with a matching or semantically similar label.

3. **Resolve Path:** If a link is found, resolve its path **relative to the directory containing the `index.md` file**.

4. **Fallback:** If the index file is missing or the link is absent, use the Standard Default Paths below.

5. **Verify:** You MUST verify the resolved file actually exists on disk.

**Standard Default Paths (Project):**
- **Product Definition**: `conductor/product.md`
- **Tech Stack**: `conductor/tech-stack.md`
- **Workflow**: `conductor/workflow.md`
- **Product Guidelines**: `conductor/product-guidelines.md`
- **Tracks Registry**: `conductor/tracks.md`
- **Tracks Directory**: `conductor/tracks/`
- **Superconductor Runs**: `conductor/superconductor/`

**Standard Default Paths (Track):**
- **Specification**: `conductor/tracks/<track_id>/spec.md`
- **Implementation Plan**: `conductor/tracks/<track_id>/plan.md`
- **Metadata**: `conductor/tracks/<track_id>/metadata.json`

---

## Command Protocols

### /conductor:setup - Project Initialization

**SYSTEM DIRECTIVE:** Initialize Conductor for a new or existing project.

**CRITICAL:** Validate the success of every tool call. If any tool call fails, halt immediately, announce the failure, and await instructions.

#### Phase 1: Resume Check (Project Audit)

1. **Audit Artifacts:** Check for existing files in the `conductor/` directory:
   - `product.md`, `product-guidelines.md`, `tech-stack.md`
   - `code_styleguides/`, `workflow.md`, `index.md`
   - `tracks/*/` (specifically `plan.md` and `index.md`)

2. **Determine Resume Point:** Map the project's state using this priority table (highest match wins):

| Artifact Exists | Resume At | Announcement |
|:---|:---|:---|
| All files in `tracks/<track_id>/` | **HALT** | "Project already initialized. Use `/conductor:newTrack` or `/conductor:implement`." |
| `index.md` (top-level) | Phase 4 | "Resuming: Scaffolding complete. Next: generate first track." |
| `workflow.md` | Phase 3.5 | "Resuming: Workflow defined. Next: generate index." |
| `code_styleguides/` | Phase 3.5 | "Resuming: Guides configured. Next: define workflow." |
| `tech-stack.md` | Phase 3.4 | "Resuming: Tech Stack defined. Next: select Code Styleguides." |
| `product-guidelines.md` | Phase 3.3 | "Resuming: Guidelines complete. Next: define Technology Stack." |
| `product.md` | Phase 3.2 | "Resuming: Product Guide complete. Next: create Product Guidelines." |
| (None) | Phase 2 | Start from scratch |

#### Phase 2: Project Discovery

1. **Detect Project Maturity:**
   - **Brownfield Indicators:** `.git` with history, `package.json`, `requirements.txt`, `go.mod`, `Cargo.toml`, `pom.xml`, `src/`, `app/`, `lib/`
   - **Greenfield:** Empty or only `README.md`, no dependency manifests or source code

2. **For Brownfield Projects:**
   - Announce existing project detected with specific indicator found
   - Warn about uncommitted changes if `git status --porcelain` shows any outside `conductor/`
   - Request permission for read-only analysis
   - Analyze codebase structure respecting `.gitignore` patterns
   - Prioritize key files: manifests, configs, README
   - For large files (>1MB): read only first/last 20 lines
   - Extract: Language, Frameworks, Database, Architecture pattern

3. **For Greenfield Projects:**
   - Initialize git if needed: `git init`
   - Ask: "What do you want to build?"
   - Create `conductor/` directory

#### Phase 3: Interactive Context Generation

Use `AskUserQuestion` tool for each section. For each section, offer **Interactive** vs **Autogenerate** modes. Batch up to 4 related questions per tool call.

**3.1 Product Guide (`product.md`):**
- Target users and personas
- Product goals and vision
- Key features and capabilities
- Success metrics
- **Brownfield:** Formulate questions aware of analyzed codebase; don't ask what's already evident
- Draft document, present for approval, revise until confirmed

**3.2 Product Guidelines (`product-guidelines.md`):**
- Prose style and tone
- Brand messaging
- Visual identity principles
- UX principles
- **Brownfield:** Analyze current docs/code to suggest guidelines matching established style

**3.3 Tech Stack (`tech-stack.md`):**
- **Brownfield:** State inferred stack, ask for confirmation. If disputed, allow manual correction
- **Greenfield:** Languages, frameworks, databases, infrastructure
- Separate concerns across questions (Language, Backend, Frontend, Database)
- Allow multi-select for hybrid stacks

**3.4 Code Styleguides:**
- List available guides from `templates/code_styleguides/`
- **Brownfield:** Auto-select based on inferred stack, offer to add more
- **Greenfield:** Recommend based on chosen stack, allow selection from library
- Copy selected guides to `conductor/code_styleguides/`

**3.5 Workflow (`workflow.md`):**
- Copy template from `templates/workflow.md`
- Offer Default vs Customize modes
- Customizable: Test coverage %, commit strategy (per-task vs per-phase), summary storage (git notes vs commit messages)
- Present final configuration for confirmation

**3.6 Generate Project Index (`conductor/index.md`):**
- Create `conductor/index.md` linking to all generated artifacts
- This serves as the master navigation for the Universal File Resolution Protocol

#### Phase 4: Initial Track Generation

1. **Gather Requirements** (greenfield only): User stories, functional requirements
2. **Check for duplicate track names** against existing tracks directory
3. **Propose Initial Track:** Single track title based on context
4. **Generate Artifacts:**
   - Generate Track ID: `shortname_YYYYMMDD`
   - Create `conductor/tracks/<track_id>/`
   - Write `metadata.json`, `spec.md`, `plan.md`, `index.md`
   - Update `conductor/tracks.md`
5. **Commit:** `conductor(setup): Add conductor setup files`

#### Question Format

Always use `AskUserQuestion` with this structure:
- 2-3 suggested options based on context (with descriptions)
- "Other" is automatically provided for custom input
- For additive questions (scope, features): `multiSelect: true`
- For exclusive choices (primary tech): `multiSelect: false`

---

### /conductor:superconductor — Autonomous Full-Pipeline Execution

This command is handled by the **superconductor** skill and CLI.

Install the superconductor skill, then run from your terminal:

```bash
# Terminal 1: start app-server
codex app-server --listen ws://127.0.0.1:4500

# Terminal 2: run superconductor
superconductor run <repo> --spec <requirements.md>
```

The superconductor CLI controls the loop externally via WebSocket. The agent receives focused per-wave assignments and cannot decide when to stop. See the superconductor skill for full documentation.

---

### /conductor:newTrack - Create New Track

**SYSTEM DIRECTIVE:** Create a new feature or bug fix track.

**CRITICAL:** Validate the success of every tool call. If any tool call fails, halt immediately, announce the failure, and await instructions.

#### Phase 1: Setup Verification

Verify existence of (via Universal File Resolution Protocol):
- **Product Definition**
- **Tech Stack**
- **Workflow**

If missing: "Conductor not set up. Run `/conductor:setup` first."

#### Phase 2: Track Definition

1. **Get Description:** From args or ask user
2. **Infer Type:** Feature, Bug, Chore, Refactor (don't ask, infer from description)
3. **Check Duplicates:** List existing track directories, extract short names. If proposed name matches an existing short name, halt and suggest choosing a different name or resuming the existing track

#### Phase 3: Interactive Spec Generation

Use `AskUserQuestion` (3-5 questions for features, 2-3 for bugs):
- Reference `product.md`, `tech-stack.md` for context-aware questions
- Batch up to 4 related questions per tool call
- Provide 2-3 plausible options per question
- Classify each question as **Additive** (multi-select) or **Exclusive Choice** (single-select)
- Generate comprehensive `spec.md`:
  - Overview
  - Functional Requirements
  - Non-Functional Requirements
  - Acceptance Criteria
  - Out of Scope
- Present full draft for user approval, revise until confirmed

#### Phase 4: Plan Generation

1. Read confirmed spec and **Workflow**
2. Generate hierarchical `plan.md`:
   - Phases with checkpoints
   - Tasks with `[ ]` markers for EVERY task and sub-task
   - Sub-tasks following workflow (e.g., TDD: Write Tests -> Implement)
3. **Inject Phase Completion Tasks:** If "Phase Completion Verification and Checkpointing Protocol" exists in Workflow, append to each phase: `- [ ] Task: Conductor - User Manual Verification '<Phase Name>' (Protocol in workflow.md)`
4. Present full draft for user approval, revise until confirmed

#### Phase 5: Artifact Creation

1. **Generate Track ID:** `shortname_YYYYMMDD`
2. **Create Directory:** `conductor/tracks/<track_id>/`
3. **Write Files:**
   - `metadata.json` with track_id, type, status, timestamps
   - `spec.md`
   - `plan.md`
   - `index.md` linking to spec, plan, and metadata
4. **Update Tracks Registry (`tracks.md`):**
   ```markdown
   ---
   ## [ ] Track: <Description>
   *Link: [./conductor/tracks/<track_id>/](./conductor/tracks/<track_id>/)*
   ```
5. **Announce:** Ready for `/conductor:implement`

#### Integration: Scrum Optimization (Optional)

After track creation, if the plan contains multiple phases with parallelizable tasks:
- Suggest running the **scrum** skill to optimize the plan for multi-agent execution
- The scrum skill will invoke **dependency-graph** for DAG analysis
- Outputs individual task files compatible with conductor's implement workflow

---

### /conductor:implement - Execute Track

**SYSTEM DIRECTIVE:** Implement tasks from a track's plan.

**CRITICAL:** Validate the success of every tool call. If any tool call fails, halt immediately, announce the failure, and await instructions.

#### Phase 1: Track Selection

1. Check for user-provided track name
2. Parse **Tracks Registry** by splitting content by `---` separator to identify each track section. Extract status (`[ ]`, `[~]`, `[x]`), description, and link
3. **If track specified:** Exact case-insensitive match, confirm with user
4. **If ambiguous match:** Ask user to clarify with the exact track name
5. **If no track specified:** Select first incomplete track (`[ ]` or `[~]`), confirm with user
6. **If no incomplete tracks:** Announce all tasks completed, halt

#### Phase 2: Track Setup

1. Update track status to `[~]` (in progress) in **Tracks Registry**
2. Load context (via Universal File Resolution Protocol):
   - Track's **Implementation Plan**
   - Track's **Specification**
   - **Workflow**
3. **Activate Relevant Skills:** If skills are installed in workspace, identify any relevant to the track's spec and plan. Read and apply their guidelines during execution

#### Phase 3: Task Execution

For each task in the **Implementation Plan**, follow **Workflow** procedures:

1. **Mark In Progress:** `[ ]` -> `[~]`
2. **Defer to Workflow:** The Workflow file is the **single source of truth** for the task lifecycle. Follow its "Task Workflow" section precisely:
   - TDD Workflow (if specified): Write failing tests (Red) -> Implement to pass (Green) -> Refactor (optional)
   - Verify Coverage: Run test coverage tools with `CI=true` for non-interactive execution
   - Document Deviations: If implementation differs from tech stack, STOP, update `tech-stack.md` first, then resume
3. **Commit Code:** Conventional commit message
4. **Attach Git Note:** Task summary with details using `git notes add -m "<note>" <commit_hash>`
5. **Update Plan:** Mark `[x]` with first 7 chars of commit SHA
6. **Commit Plan Update:** `conductor(plan): Mark task '<task_name>' complete`

#### Phase 4: Phase Completion Protocol

When a phase completes:

1. **Ensure Test Coverage:** Determine phase scope via previous checkpoint SHA. Use `git diff --name-only <prev_checkpoint> HEAD` to list changed files. Verify test files exist for each code file; create missing tests
2. **Execute Tests:** Run with `CI=true` for non-interactive. If tests fail, attempt fix max 2 times, then halt and ask user for guidance
3. **Manual Verification:** Present detailed, actionable step-by-step verification plan:
   - For frontend: specific URLs, expected visual state
   - For backend: specific curl commands, expected responses
4. **Await Confirmation:** User must explicitly approve. Do not proceed without explicit yes
5. **Create Checkpoint:** Commit with verification report as git note
6. **Update Plan:** Add `[checkpoint: <sha>]` to phase heading
7. **Commit Plan Update:** `conductor(plan): Mark phase '<phase_name>' as complete`

#### Phase 5: Track Finalization

1. Update **Tracks Registry**: `[~]` -> `[x]`
2. Commit: `chore(conductor): Mark track '<description>' complete`
3. **Synchronize Documentation:**
   - Analyze spec for impacts to **Product Definition**, **Tech Stack**, **Product Guidelines**
   - For each document needing updates: propose changes with diffs, require explicit user approval
   - **Product Guidelines:** Only modify for significant strategic shifts (rebrand, fundamental change). Include WARNING in approval prompt
   - Commit approved changes: `docs(conductor): Synchronize docs for track '<description>'`

#### Phase 6: Track Cleanup

Offer options:
- **A) Review:** Run `/conductor:review` to verify changes before finalizing
- **B) Archive:** Move to `conductor/archive/`, remove from tracks file
- **C) Delete:** Permanent removal (requires double confirmation with explicit warning)
- **D) Skip:** Leave in tracks file

---

### /conductor:review - Code Review

**SYSTEM DIRECTIVE:** Review completed work against guidelines and the plan.

**Persona:** You are a Principal Software Engineer and Code Review Architect. Think from first principles. Meticulous, detail-oriented. Prioritize correctness, maintainability, and security over stylistic nits.

**CRITICAL:** Validate the success of every tool call. If any tool call fails, halt immediately, announce the failure, and await instructions.

#### Phase 1: Setup Check

Verify existence of (via Universal File Resolution Protocol):
- **Tracks Registry**, **Product Definition**, **Tech Stack**, **Workflow**, **Product Guidelines**

If missing: "Conductor not set up. Run `/conductor:setup` first."

#### Phase 2: Identify Scope

1. **If args provided:** Use as target scope
2. **If no args:** Check Tracks Registry for `[~]` In Progress track, confirm with user
3. **If no track in progress:** Ask user what to review
4. **Confirm scope** with user before proceeding

#### Phase 3: Retrieve Context

1. **Load Project Context:**
   - Read `product-guidelines.md` and `tech-stack.md`
   - Read ALL `.md` files in `conductor/code_styleguides/` - violations here are **High** severity
2. **Load Track Context (if reviewing a track):**
   - Read the track's `plan.md`
   - Extract recorded commit SHAs, determine revision range
3. **Smart Chunking for Large Changes:**
   - Run `git diff --shortstat <range>` first
   - **< 300 lines:** Full diff in one pass
   - **> 300 lines:** Confirm with user, then iterate file-by-file (skip locks/assets), aggregate findings

#### Phase 4: Analyze and Verify

1. **Intent Verification:** Does code implement what `plan.md` and `spec.md` asked for?
2. **Style Compliance:** Against `product-guidelines.md` AND `code_styleguides/*.md`
3. **Correctness & Safety:** Bugs, race conditions, null pointer risks. Security scan for hardcoded secrets, PII leaks, unsafe input handling
4. **Testing:** New tests present? Coverage adequate? **Execute test suite automatically** (infer command from project structure)
5. **Skill-Specific Checks:** If relevant skills installed, verify compliance with their best practices

#### Phase 5: Output Findings

```markdown
# Review Report: [Track Name / Context]

## Summary
[Single sentence on overall quality and readiness]

## Verification Checks
- [ ] **Plan Compliance**: [Yes/No/Partial] - [Comment]
- [ ] **Style Compliance**: [Pass/Fail]
- [ ] **New Tests**: [Yes/No]
- [ ] **Test Coverage**: [Yes/No/Partial]
- [ ] **Test Results**: [Passed/Failed] - [Summary]

## Findings
*(Only if issues found)*

### [Critical/High/Medium/Low] Description of Issue
- **File**: `path/to/file` (Lines L<Start>-L<End>)
- **Context**: [Why this is an issue]
- **Suggestion**:
```diff
- old_code
+ new_code
```
```

#### Phase 6: Review Decision

- **Critical/High issues:** "I recommend fixing important issues before moving forward."
- **Medium/Low only:** "Changes look good overall, with a few suggestions."
- **No issues:** "Everything looks great."

Offer: Apply Fixes (automatic) | Manual Fix (user edits) | Complete Track (proceed despite warnings)

#### Phase 7: Commit Review Changes

If changes were applied:
1. Stage code changes, commit: `fix(conductor): Apply review suggestions for track '<name>'`
2. Update `plan.md` with new "Review Fixes" phase, record SHA
3. Commit plan update: `conductor(plan): Mark task 'Apply review suggestions' complete`

#### Phase 8: Track Cleanup

Same as implement cleanup: Archive | Delete | Skip

---

### /conductor:status - Progress Overview

**SYSTEM DIRECTIVE:** Display project progress summary.

**CRITICAL:** Validate the success of every tool call. If any tool call fails, halt immediately, announce the failure, and await instructions.

1. **Verify Setup:** Check for **Tracks Registry**, **Product Definition**, **Tech Stack**, **Workflow** (via Universal File Resolution Protocol)
2. **Read All Plans:** Parse Tracks Registry (handle both `- [ ] **Track:` and `## [ ] Track:` formats) and all track `plan.md` files
3. **If superconductor run exists:** Also read `requirements-matrix.json` and report:
   - Requirements: verified/implemented/in-track/pending (counts)
   - Current stage of the superconductor pipeline
4. **Generate Report:**
   - Current Date/Time
   - Project Status (On Track / Behind / Blocked)
   - Current Phase and Task (in progress)
   - Next Action (pending)
   - Blockers (if any)
   - Phases (total count)
   - Tasks (total count)
   - Progress: completed/total (percentage%)

---

### /conductor:revert - Git-Aware Revert

**SYSTEM DIRECTIVE:** Revert logical units of work (Tracks, Phases, Tasks).

**CRITICAL:** Validate the success of every tool call. If any tool call fails, halt immediately, announce the failure, and await instructions. User confirmation required at multiple checkpoints.

#### Phase 1: Target Selection

1. **If target provided:** Confirm with user (Path A: Direct Confirmation)
2. **If no target (Path B: Guided Selection Menu):**
   - Scan all plans for in-progress items (`[~]`)
   - Fallback to 3 most recently completed items (`[x]`)
   - Present unified hierarchical menu (max 4 items) with Track grouping
   - "Other" option automatically provided

#### Phase 2: Git Reconciliation

1. Find implementation commits from plan SHAs
2. **Handle Ghost Commits:** If SHA not found in git (rewritten history from rebase/squash), search log for similar commit message, ask user to confirm replacement
3. Find plan-update commits (commits after implementation that modified the plan file)
4. For track reverts: Find track creation commit via `git log -- <tracks_registry_path>`
5. Check for merge commits and cherry-pick duplicates, warn about complexities

#### Phase 3: Execution Plan

Present summary:
- Target description
- Commits to revert (with messages and SHAs)
- Action to take

Offer: Approve | Revise (allow user to modify the plan)

#### Phase 4: Execution

1. Run `git revert --no-edit <sha>` in reverse chronological order
2. Handle conflicts with user guidance
3. Verify plan state after revert — fix if needed
4. Announce completion

---

## Integration Points

### Tools to Use

- **`AskUserQuestion`/`ask_user`**: Interactive prompts with typed options
- **`TodoWrite`**: Track progress through tasks and phases
- **`Read/Write/Edit`**: File operations
- **`Bash`**: Git commands, test execution
- **`Glob/Grep`**: File discovery
- **`SubAgent/Superpowers`**: Worker fan-out for parallel track execution

### Companion Skills

- **`scrum`**: Optimize plans for parallel multi-agent execution with dependency analysis, verification gates, and context budget management. Invoke after `/conductor:newTrack` for complex plans. **Automatically invoked by superconductor Stage 7** for multi-phase tracks.
- **`dependency-graph`**: Generate architectural dependency graphs. Used by scrum for DAG analysis, or independently via `/dependency-graph` for codebase visualization.
- **`forensic-genesis`**: Deep forensic codebase analysis for brownfield projects. Can be used during setup for comprehensive code review before track creation.
- **`architect`**: Drive brownfield intent alignment, claim classification, and final sufficiency decisions for `/conductor:superconductor`.
- **`curiosity`**: Generate graph-negative-space investigation questions and docs/code drift checks during `/conductor:superconductor`.
- **`forensic-ingest`**: Build code notebooks and the NotebookLM harness dump used by workers for JIT context.
- **`sequential-thinking`**: Used by superconductor for closure ordering (Stage 4), plan sequencing (Stage 7), and driver-level decisions.

### MCP Servers (When Available)

- **Context7**: Fetch library documentation for tech stack decisions
- **Exa**: Research best practices for technologies. **Only use when the track involves external APIs, libraries, or current-year best practices.** Do not use for purely internal code changes.
- **Linear**: Sync tracks with Linear issues (optional)
- **CGC**: Primary brownfield graph surface for intent-to-code verification and anomaly hunting. Used in superconductor Stages 3 and 5.
- **NotebookLM**: Harness dump and worker retrieval layer; refresh superseded sources instead of allowing stale duplicates.

---

## Quality Gates

Before marking any task complete, verify:
- [ ] All tests pass
- [ ] Code coverage meets requirements (default >80%)
- [ ] Follows project code style guidelines (as defined in `code_styleguides/`)
- [ ] Public functions/methods documented (docstrings, JSDoc, etc.)
- [ ] Type safety enforced (type hints, TypeScript types, etc.)
- [ ] No linting or static analysis errors
- [ ] Works on target platforms
- [ ] No security vulnerabilities introduced
- [ ] Documentation updated if needed

---

## Commit Message Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:** feat, fix, docs, style, refactor, test, chore
**Conductor-specific:** `conductor(setup)`, `conductor(plan)`, `conductor(checkpoint)`, `conductor(superconductor)`

---

## Definition of Done

A task is complete when:

1. All code implemented to specification
2. Unit tests written and passing
3. Code coverage meets project requirements
4. Documentation complete (if applicable)
5. Code passes all configured linting and static analysis checks
6. Works correctly on target platforms
7. Implementation notes added to `plan.md`
8. Changes committed with proper message
9. Git note with task summary attached to the commit

## Emergency Procedures

### Critical Bug in Production
1. Create hotfix branch from main
2. Write failing test for bug
3. Implement minimal fix
4. Test thoroughly
5. Deploy immediately
6. Document in plan.md

### Security Breach
1. Rotate all secrets immediately
2. Review access logs
3. Patch vulnerability
4. Notify affected users (if any)
5. Document and update security procedures
