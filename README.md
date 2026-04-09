# David Harness

Personal skill registry for Claude Code and OpenAI Codex CLI. Contains all custom skills, commands, agent configurations, and the Hephaestus autonomous deep worker infrastructure.

## Structure

```
david-harness/
├── claude/                    # Claude Code skill registry
│   ├── skills/                # SKILL.md-based skills (symlink to ~/.claude/skills/)
│   ├── commands/              # Slash commands (copy to ~/.claude/commands/)
│   └── plugins/               # Third-party plugin install instructions
├── codex/                     # OpenAI Codex CLI skill registry
│   ├── skills/                # SKILL.md-based skills (copy to ~/.codex/skills/)
│   ├── agents/                # Agent configs (copy to ~/.codex/agents/)
│   └── AGENTS.md              # Global Hephaestus identity
├── hephaestus/                # Hephaestus runner infrastructure
│   ├── INSTALL.md             # Full install guide
│   ├── run.sh                 # CLI runner script
│   └── agents/                # Agent config files
└── setup/                     # Installation scripts and dependency manifest
    ├── install-claude.sh      # Symlink Claude skills
    ├── install-codex.sh       # Symlink Codex skills
    └── dependencies.md        # All required packages
```

## Skills Inventory

### Shared Skills (present in both Claude and Codex registries)

| Skill | Description |
|-------|-------------|
| `agent-browser-interactive` | Persistent browser automation via agent-browser CLI |
| `conductor` | Context-driven spec-to-plan-to-implement workflow |
| `crispy` | QRSPI protocol for large/ambiguous tasks |
| `exa` | Web research via local Exa Python scripts |
| `hephaestus` | Delegate deep work to gpt-5.4 via Codex |
| `hygene` | Kijko repo GitHub hygiene and RACI enforcement |
| `launch-app-server-agents` | Launch Codex app-server sessions on Hetzner |
| `macbox` | macOS sandbox/noVNC terminal command patterns |
| `nlm` | NotebookLM CLI operations |
| `nlm-dual-notebook-architecture` | Large codebase ingestion pattern for NLM |
| `peep` | Semi-formal certificate-based code reasoning |
| `proofshot` | Visual UI verification with video recording |
| `trace2skill` | Session-trace analysis and skill-patch extraction from `.codex` and `.claude` runs |
| `superconductor` | Autonomous spec-to-verified execution pipeline |
| `uncommon-sense` | Hidden requirement inference and orchestration |

### Claude-Only

| Skill | Description |
|-------|-------------|
| `forensic-genesis` | Forensic codebase analysis with validation loops |
| `forensic-ingest` | Codebase ingestion into NotebookLM |
| `openai-docs` | OpenAI docs lookup via developers.openai.com MCP |

### Codex-Only

| Skill | Description |
|-------|-------------|
| `kijko-memory` | Episodic memory CLI integration for Codex sessions |

### Claude Commands (slash commands)

| Command | Description |
|---------|-------------|
| `/recall` | Search episodic memory across all past sessions |
| `/remember` | Store curated facts in episodic memory |
| `/verbatim` | Raw session excerpt search from memory |
| `/memory-status` | Show kijko-memory system status |

## Quick Install

```bash
# Clone
git clone https://github.com/david-kijko/david-harness.git
cd david-harness

# Install Claude skills
./setup/install-claude.sh

# Install Codex skills
./setup/install-codex.sh

# Install Hephaestus
# See hephaestus/INSTALL.md for full instructions
sudo cp hephaestus/run.sh /usr/local/bin/hephaestus
```

## Third-Party Plugins

These are installed via the Claude Code / Codex plugin marketplaces, not from this repo:

- **superpowers** (claude-plugins-official) - Workflow discipline skills
- **hookify** (claude-plugins-official) - Hook rule management
- **frontend-design** (claude-plugins-official) - UI component generation
- **chrome-devtools-mcp** (claude-plugins-official) - Browser DevTools integration
- **codex sidecar-supervisor** - Codex delegation from Claude Code
- **skill-creator** (claude-plugins-official) - Skill authoring tools
- **agent-sdk-dev** (claude-plugins-official) - Agent SDK verification
- **code-simplifier** (claude-plugins-official) - Code quality agent
- **context7** (claude-plugins-official) - Library documentation MCP

See [claude/plugins/PLUGINS.md](claude/plugins/PLUGINS.md) for detailed install instructions.

## Dependencies

See [setup/dependencies.md](setup/dependencies.md) for the full dependency manifest.

## Architecture

```
Claude Code ──── delegates ────> Hephaestus CLI ──> codex exec (gpt-5.4)
    │                                 │
    ├── ~/.claude/skills/             ├── ~/.codex/AGENTS.md (identity)
    ├── ~/.claude/commands/           ├── ~/.codex/skills/
    └── ~/.claude/plugins/            └── ~/.codex/config.toml
```

Claude Code is the orchestrator. Codex/Hephaestus is the autonomous deep worker. Skills are structured as SKILL.md files with YAML frontmatter, optional `agents/`, `references/`, `scripts/`, and `templates/` subdirectories.
