# Dependencies

All packages and tools required by the skills in this harness.

## Core Tools

| Tool | Required By | Install |
|------|-------------|---------|
| Claude Code | All Claude skills | `npm install -g @anthropic-ai/claude-code` |
| Codex CLI | Hephaestus, Codex skills | `npm install -g @openai/codex` |
| Node.js >= 18 | Claude Code, Codex, superconductor | [nodejs.org](https://nodejs.org) |
| Python >= 3.10 | exa, uncommon-sense, kijko-memory | System or `pyenv` |
| Bash >= 4 | All shell scripts | System |

## Python Packages

| Package | Required By | Install |
|---------|-------------|---------|
| `exa-py` | exa skill | `pip install exa-py` |
| `kijko-memory` | recall, remember, verbatim, memory-status | `pip install kijko-memory` or from source |

## Node Packages

| Package | Required By | Install |
|---------|-------------|---------|
| `ws` | superconductor (websocket) | `cd codex/skills/superconductor && npm install` |
| `@anthropic-ai/claude-code` | Claude Code | `npm install -g @anthropic-ai/claude-code` |
| `@openai/codex` | Hephaestus, Codex skills | `npm install -g @openai/codex` |

## CLI Tools

| Tool | Required By | Install |
|------|-------------|---------|
| `agent-browser` | agent-browser-interactive | See [agent-browser repo](https://github.com/nicepkg/agent-browser) |
| `nlm` | nlm, nlm-dual-notebook-architecture, forensic-ingest | `pip install notebooklm-cli` or from source |
| `hephaestus` | hephaestus skill | `sudo cp hephaestus/run.sh /usr/local/bin/hephaestus` |
| `gh` | hygene (GitHub operations) | `apt install gh` or [cli.github.com](https://cli.github.com) |
| `repomix` | forensic-ingest | `npm install -g repomix` |

## MCP Servers

| Server | Required By | Config Location |
|--------|-------------|-----------------|
| chrome-devtools-mcp | chrome-devtools skill | Claude plugin auto-configures |
| context7 | context7 plugin | Claude plugin auto-configures |
| notebooklm-mcp | nlm skill (Codex) | `~/.codex/config.toml` |
| sequential-thinking | Codex reasoning | `~/.codex/config.toml` |
| CodeGraphContext | Codex code graph | `~/.codex/config.toml` (optional) |

## API Keys

| Key | Required By | Where to Set |
|-----|-------------|--------------|
| `POE_API_KEY` | Hephaestus (gpt-5.4 access) | `~/.bashrc` or `~/.codex/shell_snapshots/` |
| `EXA_API_KEY` | exa skill | `~/.bashrc` |
| `ANTHROPIC_API_KEY` | Claude Code | `~/.bashrc` |
| `NLM_MCP_HETZNER_DEV_TOKEN` | nlm MCP server | `~/.bashrc` |

## Optional

| Tool | Required By | Install |
|------|-------------|---------|
| `cgc` (CodeGraphContext) | Code graph MCP | `pip install codegraphcontext` |
| Docker | forensic-ingest, deployment | System |
| `bwrap` | Codex sandbox (often bypassed) | `apt install bubblewrap` |
