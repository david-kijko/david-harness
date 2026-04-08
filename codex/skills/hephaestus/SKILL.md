---
name: hephaestus
description: 'Invoke Hephaestus (gpt-5.4) as an autonomous deep worker for complex
  implementation tasks. Triggers: ''hephaestus'', ''codex'', ''deep work'', ''send
  to codex'', ''have codex do it'', ''delegate to hephaestus'', or when facing multi-file
  implementation tasks that benefit from a dedicated craftsman with end-to-end completion
  guarantee.'
allowed-tools:
- Bash
- Read
- Write
- Edit
- Glob
- Grep
- Task
- TaskCreate
- TaskUpdate
- TaskList
---

# /hephaestus - Autonomous Deep Worker (gpt-5.4)

Hephaestus is the OmO autonomous deep worker — gpt-5.4 with a Senior Staff Engineer identity, completion guarantee, and structured execution discipline. Named after the Greek god of forge and craftsmanship.

**Model**: gpt-5.4 via Poe API (high reasoning effort)
**Identity**: Extracted from oh-my-opencode (`/home/devuser/oh-my-opencode/src/agents/hephaestus.ts`)
**Global AGENTS.md**: `~/.codex/AGENTS.md` (auto-injected into every codex session)

## Architecture

```
Claude Code (you) --- delegates task ---> hephaestus CLI ---> codex exec (gpt-5.4)
                                              |
                                    ~/.codex/AGENTS.md (Hephaestus identity)
                                              |
                                    Project AGENTS.md (if exists, layers on top)
                                              |
                                    Output captured to ~/.hephaestus/outputs/
```

Codex natively loads `~/.codex/AGENTS.md` as global instructions. Per-project `AGENTS.md` files layer on top without clobbering. The Hephaestus identity (completion guarantee, intent gate, execution loop, verification discipline) is always active.

## When to Use Hephaestus

**DELEGATE to Hephaestus when:**
- Deep implementation: multi-file features, complex refactoring, end-to-end wiring
- Second perspective: when you want a different model's take on implementation
- Autonomous completion: tasks where "100% or nothing" discipline matters
- Code generation: large-scale scaffolding, boilerplate, migration scripts
- Research + implement: "explore the codebase and build X" — Hephaestus excels at this
- User explicitly requests: "send to codex", "have hephaestus do it", "delegate"

**DO NOT delegate when:**
- Task needs current conversation context (Hephaestus has no memory of this session)
- Task requires Claude-specific tools (MCP servers, NotebookLM, Linear, Zulip)
- Simple edits (<10 lines, single file) — faster to do yourself
- Task requires interactive user dialogue — Hephaestus runs non-interactively

## Invocation Methods

### Method 1: CLI via Bash (Recommended)

```bash
# Simple task
hephaestus "Add error handling to all API routes in src/api/"

# With specific working directory
hephaestus "Refactor the auth module" --dir /home/devuser/my-project

# From a detailed brief file
hephaestus --file /tmp/task-brief.md --dir /home/devuser/my-project

# With write access (for implementation tasks)
hephaestus "Implement the user settings page" --full-auto

# Pipe task from stdin
echo "Fix all TypeScript errors in src/" | hephaestus -

# With dangerous full access (use sparingly)
hephaestus "Run the full test suite and fix all failures" --dangerous
```

### Method 2: Direct codex exec (When you need more control)

```bash
POE_API_KEY="$POE_API_KEY" codex exec \
  -m gpt-5.4 \
  -c 'model_reasoning_effort="high"' \
  -s read-only \
  -C /path/to/project \
  -o /tmp/hephaestus-output.md \
  "Your task description here"
```

### Method 3: Brief file (For complex tasks)

Write a detailed brief, then pass it:

```bash
# Write brief with full context
cat > /tmp/brief.md << 'BRIEF'
## Context
Project: my-app at /home/devuser/my-app
Stack: FastAPI + SQLAlchemy + PostgreSQL

## Task
Implement the user authentication system:
1. JWT token generation and validation
2. Login/register endpoints
3. Auth middleware for protected routes
4. Password hashing with bcrypt

## Key Files
- src/api/routes.py — existing routes
- src/models/user.py — user model (exists)
- src/config.py — database config

## Constraints
- Follow existing patterns in src/api/
- Use existing SQLAlchemy session from src/db.py
- Tests required for all endpoints
BRIEF

hephaestus --file /tmp/brief.md --dir /home/devuser/my-app --full-auto
```

## Sandbox Modes

| Mode | Flag | Use When |
|------|------|----------|
| `read-only` | (default) | Research, analysis, code review, spec drafting |
| `workspace-write` | `--full-auto` | Implementation, refactoring, test writing |
| `danger-full-access` | `--dangerous` | Running tests, installing deps, build commands |

**Default is read-only.** Use `--full-auto` for implementation tasks. Use `--dangerous` only when Hephaestus needs to run tests or install packages.

## Output

All outputs are saved to `~/.hephaestus/outputs/hephaestus-YYYYMMDD-HHMMSS.md` and also printed to stdout. Read the output file to get Hephaestus's full response.

## Crafting Good Briefs

Hephaestus has NO context from your conversation. The brief IS the context. Include:

1. **Project location** and key file paths
2. **What exists** — don't make Hephaestus rediscover your codebase
3. **What to build** — specific, concrete deliverables
4. **Constraints** — patterns to follow, files not to touch, conventions
5. **Verification criteria** — how to know it's done

**Bad**: "Fix the auth"
**Good**: "In /home/devuser/my-app, the JWT middleware in src/middleware/auth.py doesn't validate token expiry. Add expiry checking using the `exp` claim. Existing tests are in tests/test_auth.py. Follow the pattern in src/middleware/cors.py for middleware structure."

## Integration with Claude-Flow v3

For multi-agent orchestration, Hephaestus maps to the implementation worker:

```
Level 0: [Claude: Architect]         -> Design (no deps)
Level 1: [Hephaestus: Coder]         -> Implement (depends on design)
Level 2: [Claude: Reviewer]          -> Verify (depends on implementation)
Level 3: [Claude: Optimizer]         -> Refine (depends on review)
```

Use claude-flow shared memory to pass context between stages:
```bash
# Store design for Hephaestus
npx claude-flow@v3alpha memory store --namespace collaboration --key "design" --value "..."

# Hephaestus implements, stores evidence
hephaestus --file /tmp/impl-brief.md --full-auto

# Read Hephaestus output for review
cat ~/.hephaestus/outputs/hephaestus-*.md
```

## Key Files

| File | Purpose |
|------|---------|
| `~/.codex/AGENTS.md` | Global Hephaestus identity (auto-injected by codex) |
| `~/.codex/config.toml` | Codex config (model, provider, trust) |
| `~/.hephaestus/run.sh` | Wrapper script with context injection |
| `~/.hephaestus/outputs/` | All Hephaestus output files |
| `/usr/local/bin/hephaestus` | CLI symlink |
| `/home/devuser/oh-my-opencode/src/agents/hephaestus.ts` | Original OmO source |

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `POE_API_KEY not found` | `export POE_API_KEY="..."` or check `~/.codex/shell_snapshots/` |
| Codex can't read project files | Use `--dir /path/to/project` to set working directory |
| Output truncated | Check `~/.hephaestus/outputs/` for full saved output |
| Codex ignores Hephaestus identity | Verify `~/.codex/AGENTS.md` exists and has content |
| Task too large for single call | Break into subtasks, call Hephaestus multiple times |
