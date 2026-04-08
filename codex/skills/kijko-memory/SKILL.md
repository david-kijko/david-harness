---
name: kijko-memory
description: Unified episodic memory across all coding agent sessions. Use when the user references past sessions, says remember, recall, memory, forget, past session, session history, what happened, do you remember, search history, search sessions, episodic memory, cross-reference sessions, memory status, or needs context from previous Claude Code, Codex, or Hermes conversations. Do not use for in-session file search, grep, git log, or current codebase exploration.
---

# kijko-memory — Unified Episodic Memory

Persistent cross-agent memory system. Indexes all Claude Code, Codex, and Hermes sessions into a single searchable store with hybrid BM25 + dense retrieval, RRF fusion, and GPT-5.4 semi-formal synthesis.

## Primary Commands

### Recall — LLM-synthesized answer with citations

```bash
kijko-memory --limit 5 recall "<query>"
```

Use when the user asks about past sessions, decisions, or outcomes. Returns a structured answer with PREMISES, EVIDENCE, CONCLUSION, and GAPS sections.

### Verbatim — raw session excerpts

```bash
kijko-memory --limit 5 verbatim "<query>"
```

Use when the user wants to see exactly what happened — raw tool calls, messages, commands. Returns provenance citations like `session:seq_start-seq_end`.

### Remember — store a curated fact

```bash
kijko-memory remember "<text>"
```

Stores an L3 assertion with trust=0.5. Use for infrastructure facts, project decisions, debugging outcomes, lessons learned.

### Events — search structured events

```bash
kijko-memory events "<query>"
```

Searches L2 typed events: command_run, file_changed, error, decision, git_op, entity_mention.

## Fact Management

```bash
# List all active facts
kijko-memory facts

# Search facts by keyword
kijko-memory facts "<query>"

# Remove a fact by ID
kijko-memory forget <id>

# Adjust trust: + means helpful, - means wrong/outdated
kijko-memory feedback <id> +
kijko-memory feedback <id> -
```

## Administration

```bash
# Index statistics per layer
kijko-memory stats

# Health check: timer state, last ingest, staleness
kijko-memory health

# Force incremental ingest now
kijko-memory ingest

# List recent sessions across all agents
kijko-memory sessions
```

## Filters

Apply to any retrieval command:

```bash
# Filter by agent
kijko-memory --agent codex recall "<query>"
kijko-memory --agent claude_code verbatim "<query>"

# Limit results
kijko-memory --limit 3 recall "<query>"
```

## Architecture

- **L0**: Raw immutable session transcripts (messages, tool calls, diffs)
- **L1**: Episodic summaries (LLM-generated per session)
- **L2**: Structured typed events
- **L3**: Curated assertions with trust scores
- **LIVE**: Current unfinished session (searched at query time)

Retrieval: BM25 (FTS5) + dense vector (nomic-embed-text) + RRF fusion + evidence expansion.
Synthesis: GPT-5.4 with semi-formal reasoning template.

## Auto-ingest

Sessions are indexed automatically via systemd timer every 5 minutes. Run `kijko-memory health` to verify.

## When NOT to use

- Searching the current codebase (use grep, find, rg instead)
- Git history for a specific repo (use git log)
- Real-time web search (use exa skill)
- Current file contents (use cat/read)
