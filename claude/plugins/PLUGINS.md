# Claude Code Plugin Registry

These third-party plugins provide additional skills and are installed via the Claude Code plugin system, not directly from this repo.

## Installation

Plugins are installed using the Claude Code CLI:

```bash
claude plugins install <plugin-name>@<marketplace>
```

Or via the Claude Code interactive menu: `/plugins`

## Official Plugins (claude-plugins-official marketplace)

### superpowers (v5.0.7)
Workflow discipline skills for structured development.

```bash
claude plugins install superpowers@claude-plugins-official
```

**Skills provided:**
- `superpowers:brainstorming` - Creative work exploration
- `superpowers:writing-plans` - Implementation plan authoring
- `superpowers:executing-plans` - Plan execution with review checkpoints
- `superpowers:test-driven-development` - TDD workflow
- `superpowers:systematic-debugging` - Structured debugging
- `superpowers:verification-before-completion` - Evidence-based completion
- `superpowers:requesting-code-review` - Code review requests
- `superpowers:receiving-code-review` - Review feedback handling
- `superpowers:finishing-a-development-branch` - Branch integration
- `superpowers:using-git-worktrees` - Isolated worktree management
- `superpowers:dispatching-parallel-agents` - Parallel agent coordination
- `superpowers:subagent-driven-development` - Subagent task execution
- `superpowers:writing-skills` - Skill authoring

**Agent provided:**
- `superpowers:code-reviewer` - Code review agent

---

### hookify
Hook rule management for preventing unwanted behaviors.

```bash
claude plugins install hookify@claude-plugins-official
```

**Commands:** `/hookify`, `/hookify:list`, `/hookify:configure`, `/hookify:help`
**Skills:** `hookify:writing-rules`
**Agent:** `hookify:conversation-analyzer`

---

### frontend-design
Distinctive, production-grade frontend interface generation.

```bash
claude plugins install frontend-design@claude-plugins-official
```

**Skills:** `frontend-design:frontend-design`

---

### chrome-devtools-mcp
Chrome DevTools integration via MCP for debugging and browser automation.

```bash
claude plugins install chrome-devtools-mcp@claude-plugins-official
```

**Skills:** `chrome-devtools:chrome-devtools`, `chrome-devtools:troubleshooting`, `chrome-devtools:debug-optimize-lcp`, `chrome-devtools:a11y-debugging`

**Requires:** Chrome/Chromium with remote debugging enabled

---

### skill-creator
Skill authoring, evaluation, and benchmarking tools.

```bash
claude plugins install skill-creator@claude-plugins-official
```

**Skills:** `skill-creator:skill-creator`
**Agents:** `skill-creator:comparator`, `skill-creator:grader`, `skill-creator:analyzer`

---

### agent-sdk-dev
Claude Agent SDK application verification.

```bash
claude plugins install agent-sdk-dev@claude-plugins-official
```

**Commands:** `/agent-sdk-dev:new-sdk-app`
**Agents:** `agent-sdk-dev:agent-sdk-verifier-ts`, `agent-sdk-dev:agent-sdk-verifier-py`

---

### code-simplifier
Code quality and simplification agent.

```bash
claude plugins install code-simplifier@claude-plugins-official
```

**Agent:** `code-simplifier:code-simplifier`

---

### context7
Library documentation MCP server.

```bash
claude plugins install context7@claude-plugins-official
```

**MCP tools:** `context7:resolve-library-id`, `context7:query-docs`

---

### typescript-lsp / pyright-lsp
Language server protocol integrations.

```bash
claude plugins install typescript-lsp@claude-plugins-official
claude plugins install pyright-lsp@claude-plugins-official
```

## Codex-Specific Plugin

### codex (sidecar-supervisor)
Codex delegation from Claude Code.

```bash
claude plugins install codex@sidecar-supervisor
```

**Commands:** `/codex:setup`, `/codex:rescue`, `/codex:review`, `/codex:status`, and more
**Agents:** `codex:sidecar-supervisor`, `codex:codex-rescue`
**Skills:** `codex:codex-cli-runtime`, `codex:gpt-5-4-prompting`, `codex:codex-result-handling`

## Codex Superpowers Port

Superpowers skills are also available for Codex. Install from the superpowers repo:

```bash
# Clone superpowers and symlink skills into Codex
git clone https://github.com/anthropics/superpowers.git ~/.codex/superpowers
cd ~/.codex/skills
for skill in brainstorming writing-plans executing-plans test-driven-development systematic-debugging verification-before-completion requesting-code-review receiving-code-review finishing-a-development-branch using-git-worktrees dispatching-parallel-agents subagent-driven-development writing-skills using-superpowers; do
  ln -sf ~/.codex/superpowers/skills/$skill .
done
```
