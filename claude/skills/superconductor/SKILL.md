---
name: superconductor
description: Use when the user asks Claude to launch or inspect the superconductor pipeline, autonomously execute a requirements document, or run /conductor-superconductor. Claude can invoke the superconductor CLI from Bash and inspect artifacts, while the active WebSocket target remains codex app-server on this machine.
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

# Superconductor — Autonomous Spec-to-Verified Execution

One CLI. One loop. Every requirement verified or it doesn't stop.

## What This Is

Superconductor is an external control plane that drives a codex session from
outside. It connects to `codex app-server` via WebSocket, sends focused
assignments wave by wave, and checks a hard gate after each wave. The agent
(you, if you're reading this inside a session) executes each assignment. The
CLI decides what's next.

When invoked from Claude Code, Claude can launch the CLI and inspect artifacts,
but the installed `claude` binary here does not expose `app-server`. Use
`codex app-server` as the supervisor target.

```
┌──────────────────────────────────────────────────────────────┐
│                    superconductor CLI                         │
│            (Node.js — NOT an LLM, pure code)                 │
├──────────────────────────────────────────────────────────────┤
│  1. Read requirements-matrix.json → determine state           │
│  2. Pick next N incomplete tracks                             │
│  3. turn/start → focused assignment to the agent              │
│  4. Wait for turn/completed                                   │
│  5. Gate check: ALL verified? → exit 0. Otherwise → loop.     │
│  6. turn/steer available for mid-flight corrections           │
└──────────────────────────────────────────────────────────────┘
```

## CLI Reference

### Installation

```bash
# User-writable link (run once)
mkdir -p ~/.local/bin
ln -sf ~/.claude/skills/superconductor/bin/superconductor.mjs ~/.local/bin/superconductor

# Or use directly
node ~/.claude/skills/superconductor/bin/superconductor.mjs <subcommand> ...
```

Requires: Node.js 18+ and the local `ws` dependency:

```bash
npm install --prefix ~/.claude/skills/superconductor ws
```

### Subcommands

```bash
# Full pipeline: parse spec → generate tracks → implement → verify
superconductor run <repo> --spec <requirements-file>

# Resume from where it left off (reads matrix state)
superconductor resume <repo>

# Show current status (next action, gate state, incomplete tracks)
superconductor status <repo>

# Run gate check only (exit 0 = all verified, exit 1 = work remains)
superconductor gate <repo>
```

### Options

| Option | Default | Description |
|---|---|---|
| `--spec <file>` | required for `run` | Requirements source (markdown, text, docx) |
| `--ws <url>` | `ws://127.0.0.1:4500` | App-server WebSocket URL |
| `--max-waves <n>` | 50 | Safety cap on number of turns |
| `--tracks-per-wave <n>` | 3 | Tracks assigned per turn |
| `--model <model>` | server default | Model override |
| `--run-id <id>` | auto-detect latest | Target a specific run |
| `--skill-path <path>` | auto (bundled SKILL.md) | Override skill attachment |
| `--conductor-path <path>` | - | Also attach conductor SKILL.md |
| `--dry-run` | - | Preview prompts without sending turns |

### Usage: Two Terminals

**Terminal 1 — Start the app-server:**
```bash
cd <repo-root>
codex app-server --listen ws://127.0.0.1:4500
```

**Terminal 2 — Run superconductor:**
```bash
# New run against a spec:
superconductor run /path/to/repo --spec /path/to/requirements.md

# Resume an interrupted run:
superconductor resume /path/to/repo

# Check progress:
superconductor status /path/to/repo
```

---

## For the Agent: How You Operate Under Superconductor

If you're a Claude Code / Codex agent reading this as an attached skill during
a supervised session, these are your rules.

### You Will Receive Assignments

The CLI sends you one assignment per turn. Assignment types:

#### 1. Setup (Stages 1-7)

Parse the requirements source, investigate the codebase, decompose into domain
tracks, generate all track artifacts. Do NOT start implementation.

Follow the detailed protocol in `references/pipeline.md`:
- Stage 1: Parse requirements into `requirements-matrix.json`
- Stage 2: Intent alignment — generate claims, check against harness docs
- Stage 3: Code investigation — CGC or file system analysis
- Stage 4: Closure — resolve open questions
- Stage 5: Sufficiency gate — verify all high-impact claims resolved
- Stage 6: Group requirements into domain tracks, assign track IDs
- Stage 7: Generate track directories with spec.md, plan.md, metadata.json

Set `pipeline_stage: 7` in the matrix when done. STOP. Do not implement.

#### 2. Worker Wave

You receive a list of tracks. For each track:

1. **Read** `conductor/tracks/<track_id>/spec.md` and `plan.md`
2. **Read** `conductor/workflow.md` for the task lifecycle
3. **For EVERY task** marked `[ ]` in the plan:
   - Write failing tests (if TDD workflow specified)
   - Implement the code
   - Run tests to verify
   - Mark `[x]` in plan.md with first 7 chars of commit SHA
   - Commit with conventional message: `feat(<scope>): <description>`
   - Attach git note: `git notes add -m "<summary>" <sha>`
4. **After ALL tasks `[x]`**:
   - Update `metadata.json`: `"status": "complete"`
   - Update `requirements-matrix.json`: `"status": "verified"` with evidence array
   - Commit: `conductor(superconductor): Verify <track_id>`

#### 3. Review

Verify `implemented` requirements. Run tests/checks. Update matrix status to
`verified` with evidence. Commit.

#### 4. Reconcile

Matrix shows incomplete requirements but no incomplete tracks. Read all
plan.md files, update any requirement whose track is fully `[x]` to `verified`
with evidence. Commit.

### Rules — Non-Negotiable

1. **Complete ALL assigned tracks.** Do not stop after one.
2. **Every `[ ]` becomes `[x]`.** No skipping.
3. **Do NOT declare "honest status" and stop.** The CLI checks completion.
4. **Do NOT modify any superconductor files** (bin/, templates/, references/).
5. **Do NOT copy CLI scripts into the repo.** They live in the skill directory.
6. **If blocked:** Document why in plan.md, move to next task. Do not halt.
7. **Commit conductor state changes** (matrix, plans, metadata) at end of wave.
8. **Follow conductor workflow.md** for task lifecycle (TDD, coverage, commits).

### What You Do NOT Control

- When to stop → the CLI's gate decides
- Which tracks to work on → the CLI picks them
- Whether the run is complete → the gate script checks
- When context refreshes → the CLI manages this (future: at ~50% usage)

Your job: execute each assignment fully. Let the turn end naturally.

### Conductor Context You Need

The conductor skill provides the project context structure:

```
conductor/
├── product.md              # Product vision, users, goals
├── product-guidelines.md   # Brand, voice, style
├── tech-stack.md           # Technology choices
├── workflow.md             # Task lifecycle (TDD, commits, coverage)
├── code_styleguides/       # Language-specific style guides
├── tracks.md               # Master track registry
├── tracks/<track_id>/      # Per-track artifacts
│   ├── spec.md             # What to build
│   ├── plan.md             # How to build it (tasks with [ ] markers)
│   └── metadata.json       # Track state
└── superconductor/<run>/   # Run artifacts
    └── requirements-matrix.json  # THE source of truth
```

Read `workflow.md` before implementing. It defines the exact task lifecycle:
test → implement → verify coverage → commit → git note → update plan.

### Quality Gates

Before marking any task `[x]`:
- All tests pass
- Code coverage meets requirements (default >80%)
- Follows code_styleguides/*
- Public functions documented
- Type safety enforced
- No linting errors
- No security vulnerabilities introduced
- Conventional commit message attached

---

## Architecture: Why This Exists

Ralph Wiggum is dumb persistence — same prompt, retry until string match.

Superconductor is an external control plane:

1. **Observes** — reads matrix state, tracks progress quantitatively
2. **Reacts** — steers errant sessions back via `turn/steer`
3. **Refreshes strategically** — context window resets are checkpoints, not failures. Each new window gets a sharper prompt built from current state
4. **Accumulates** — every fresh context starts with distilled knowledge of what's done, what's stuck, what to prioritize

Context refresh is a compounding advantage. The supervisor knows the full
history; the agent gets a clean, focused window every time.
