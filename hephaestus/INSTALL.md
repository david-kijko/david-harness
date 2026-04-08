# Hephaestus Installation Guide

Hephaestus is the autonomous deep worker — gpt-5.4 via Codex CLI with a Senior Staff Engineer identity, completion guarantee, and structured execution discipline.

## Prerequisites

1. **OpenAI Codex CLI** installed and authenticated
2. **gpt-5.4** model access (via Poe API or direct OpenAI)
3. **POE_API_KEY** or **OPENAI_API_KEY** set in environment

## Step 1: Install Codex CLI

```bash
# Install Codex CLI globally
npm install -g @openai/codex

# Verify
codex --version
```

## Step 2: Set Up Global Identity

Copy the AGENTS.md to the Codex config directory. This file is automatically injected into every Codex session as global instructions.

```bash
mkdir -p ~/.codex
cp codex/AGENTS.md ~/.codex/AGENTS.md
```

## Step 3: Install Codex Config

Create or update `~/.codex/config.toml`:

```toml
model = "gpt-5.4"
model_reasoning_effort = "high"
developer_instructions = """
When diagnosing issues, do not state a root cause until you have verified all assumptions.
After every pushed commit, inspect the actual CI logs before claiming success.

When installing or repairing Codex skills:
1. Treat $CODEX_HOME/skills (default ~/.codex/skills) as the personal skill discovery root.
2. Do not install personal Codex skills under ~/.agents/skills.
3. For multi-skill bundles, link each child skill directory individually.
4. After changing skill installation, verify with a fresh codex exec session.
"""

model_instructions_file = "/home/<YOUR_USER>/.codex/AGENTS.md"

[features]
multi_agent = true

[agents]
max_threads = 6
max_depth = 2

[agents.hephaestus-worker]
description = "Autonomous deep worker with completion guarantee."
config_file = "/home/<YOUR_USER>/.codex/agents/hephaestus-worker.toml"
```

## Step 4: Install Agent Config

```bash
mkdir -p ~/.codex/agents
cp hephaestus/agents/hephaestus-worker.toml ~/.codex/agents/hephaestus-worker.toml
```

## Step 5: Install the Runner Script

```bash
# Install globally
sudo cp hephaestus/run.sh /usr/local/bin/hephaestus
sudo chmod +x /usr/local/bin/hephaestus

# Create output directory
mkdir -p ~/.hephaestus/outputs
```

## Step 6: Set API Key

```bash
# Option A: Poe API (recommended)
echo 'export POE_API_KEY="your-poe-api-key"' >> ~/.bashrc

# Option B: Direct OpenAI
echo 'export OPENAI_API_KEY="your-openai-api-key"' >> ~/.bashrc

source ~/.bashrc
```

## Step 7: Verify

```bash
# Test basic invocation
hephaestus "List all files in the current directory and describe the project structure" --dir /tmp

# Check output
ls ~/.hephaestus/outputs/
```

## Usage

```bash
# Simple task
hephaestus "Add error handling to all API routes in src/api/"

# With working directory
hephaestus "Refactor the auth module" --dir ~/my-project

# From a brief file
hephaestus --file /tmp/task-brief.md --dir ~/my-project

# With full write access
hephaestus "Implement the user settings page" --full-auto

# From stdin
echo "Fix all TypeScript errors" | hephaestus -

# Dangerous mode (bypass sandbox entirely)
hephaestus "Run full test suite and fix failures" --dangerous
```

## Sandbox Modes

| Mode | Flag | Use When |
|------|------|----------|
| `dangerous` | default | All tasks (bypasses bwrap sandbox) |
| `workspace-write` | `--full-auto` | Implementation with workspace access |

## Monitoring (for Claude Code integration)

When Claude Code invokes Hephaestus, it must poll actively:

1. Run hephaestus in background
2. Poll output file every 30 seconds with `tail -5`
3. Report progress to user at each poll
4. Read and present full result when process exits

Never go silent. The user should always know what Hephaestus is doing.

## Key Files

| File | Purpose |
|------|---------|
| `~/.codex/AGENTS.md` | Global identity (auto-injected) |
| `~/.codex/config.toml` | Codex configuration |
| `~/.codex/agents/hephaestus-worker.toml` | Agent config |
| `/usr/local/bin/hephaestus` | CLI entrypoint |
| `~/.hephaestus/outputs/` | Output directory |

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `POE_API_KEY not found` | Export it in shell profile |
| Codex can't read files | Use `--dir` to set working directory |
| Output truncated | Check `~/.hephaestus/outputs/` |
| Identity not loading | Verify `~/.codex/AGENTS.md` exists |
| Sandbox blocks everything | Use `--dangerous` flag |
