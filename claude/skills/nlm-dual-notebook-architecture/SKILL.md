---
name: nlm-dual-notebook-architecture
description: |
  Pattern for ingesting large codebases (1000+ files, 10M+ chars) into NotebookLM using a
  two-notebook architecture: Skeleton (architecture, no code) + Raw Code (N notebooks with
  full source). Use when: (1) codebase too large for single NLM notebook (>50 sources / 500K chars),
  (2) need queryable code maps with routing index, (3) running multi-agent comparative research
  with findings written to dedicated NLM. Also covers parallel research team pattern (10 agents
  × Exa searches → NLM research notebook) and Hephaestus/MCP delegation boundaries.
author: Claude Code
version: 1.0.0
---

# NLM Dual-Notebook Architecture for Large Codebases

## Problem

Large codebases (5000+ files, 20MB+ source) cannot fit in a single NotebookLM notebook (50-source limit, 500K chars/source). Naively uploading leads to either incomplete ingestion or unnavigable notebooks.

## Architecture: Three-Notebook Pattern

```
┌─────────────────────────────┐
│  Skeleton NLM               │  ← Architecture navigation
│  - Dependency graph         │
│  - Layer summaries (no code)│
│  - PageRank top files       │
│  - CODE-MAP-INDEX           │  ← routing index lives here
└─────────────────────────────┘

┌─────────────────────────────┐
│  Raw Code NLM 1..N          │  ← Full source in chunks
│  - All source docs          │
│  - Merged ≤80K chars/source │
│  - Max 50 sources/notebook  │
│  - Named by subsystem       │
└─────────────────────────────┘

┌─────────────────────────────┐
│  Research NLM (optional)    │  ← Multi-agent findings
│  - One source per agent     │
│  - Executive synthesis      │
│  - NLM-queried conclusions  │
└─────────────────────────────┘
```

## Skeleton NLM — What to Include

Generate these sources (NO raw code, file listings only):

| Source Title | Content |
|---|---|
| `L1-Architecture-Overview` | metadata, PageRank top 50, layer distribution, cycles |
| `L1-Layer-{data\|infra\|presentation\|testing}` | cluster table + file lists + dep cross-refs per cluster |
| `CODE-MAP-INDEX` | subsystem → notebook_id + source_id routing table |

**Key constraint:** Layer files > 90K chars must be split. Use `add_text_source` directly, NOT subprocess, for files > 80K chars (subprocess arg limit).

```python
# Infrastructure layer split example (161K chars → 2 parts)
# Split at nearest ## header before midpoint
lines = text.split('\n')
mid = len(lines) // 2
for i in range(mid, len(lines)):
    if lines[i].startswith('## '):
        mid = i
        break
part1, part2 = '\n'.join(lines[:mid]), '\n'.join(lines[mid:])
```

## Raw Code NLM — Batch Upload Script

The batch upload script pattern for handling 500+ sources across multiple notebooks:

```python
# Key constants
MAX_CHARS_PER_UPLOAD = 80_000   # Safe for subprocess arg length limit
MAX_SOURCES_PER_NOTEBOOK = 50   # NotebookLM limit
import time

# Split oversized source files at natural ## boundaries
def split_text(text, max_chars):
    if len(text) <= max_chars:
        return [text]
    parts = []
    while text:
        if len(text) <= max_chars:
            parts.append(text); break
        cut = text.rfind('\n## ', 0, max_chars)
        if cut < max_chars // 2:
            cut = max_chars
        parts.append(text[:cut])
        text = text[cut:]
    return parts

# Upload queue: (title, text) pairs
# Create new notebook when batch_size == MAX_SOURCES_PER_NOTEBOOK
# Always sleep(1) between uploads for rate limiting
# Save registry JSON after each notebook in case of interruption
```

**Typical scale for large repos (5000+ files):**
- ~541 source files → 711 upload items (after splitting) → 15 notebooks
- Upload time: ~90 minutes at 1s rate limit

## CODE-MAP-INDEX Format

The routing document that makes the whole system queryable:

```markdown
# CODE MAP INDEX — {project}

## Notebook Directory
| # | Notebook ID | Title | Sources |
|---|-------------|-------|---------|
| S | `{skeleton_id}` | Skeleton | N |
| 1 | `{raw_1_id}` | Raw-1 | 50 |
...

## Query Routing Guide
| Question Type | Query Target |
|---|---|
| Architecture overview | Skeleton (all sources) |
| Raw code for subsystem | Raw NB #{n}: source title matching subsystem |
| PageRank / centrality | Skeleton: L1-Architecture-Overview |

## Subsystem → Raw Notebook Mapping
| Subsystem | Layer | Files | LOC | Raw NB# |
|---|---|---|---|---|
...
```

Save as both:
- `/tmp/forensic-ingest/CODE-MAP-INDEX.md` (upload to Skeleton NLM)
- `/tmp/forensic-ingest/{project}-registry.json` (machine-readable routing)

## Registry JSON Schema

```json
{
  "project": "org/repo",
  "date": "YYYY-MM-DD",
  "skeleton": {
    "notebook_id": "...",
    "title": "Forensic Ingest: {Name}-Skeleton ({date})",
    "sources": {"L1-Architecture-Overview": "source_id", ...}
  },
  "raw_notebooks": [{"id": "...", "title": "...", "num": 1}],
  "total_raw_sources": 706,
  "clusters": {
    "subsystem-name": {
      "layer": "infrastructure",
      "file_count": 12,
      "total_loc": 1200,
      "centrality": 0.003,
      "files": ["path/to/file.go"],
      "raw_sources": [{"title": "...", "source_id": "...", "notebook_id": "...", "notebook_num": 1}]
    }
  },
  "pagerank_top50": {"path/to/file.go": 0.0047}
}
```

## Multi-Agent Research Team Pattern

For comparative research between two systems (e.g., Coder vs Sandra):

### Team Structure
```
10 agents × 1 research dimension each
  - Each agent: 2 Exa searches + NLM queries + write /tmp/research/{N}-{topic}.md
  - All run in parallel via Agent tool with run_in_background=true
  - Lead: collects files, uploads to research NLM, queries for synthesis
```

### Research Dimensions (10-axis template)
1. Provisioning / Lifecycle management
2. Time-travel / State snapshots
3. Networking architecture
4. IDE integration
5. Security (auth, RBAC, secrets)
6. AI integration
7. Enterprise features (HA, multi-tenancy, audit)
8. Storage architecture
9. Template / Preset systems
10. Integration opportunities (synthesis)

### Agent Prompt Template
```
You are a research agent. Task: compare {DIMENSION} between {SYSTEM_A} and {SYSTEM_B}.

Context:
- {SYSTEM_A}: [3-4 bullet facts]
- {SYSTEM_B}: [3-4 bullet facts]

Tasks:
1. Run 2 Exa searches: "{specific query 1}", "{specific query 2}"
2. Write findings to /tmp/forensic-ingest/research/{N}-{topic}.md covering:
   - How each system approaches this
   - Strengths/weaknesses
   - Integration opportunities
```

### Upload Pattern
```python
# After all agents complete:
for fname, title in sorted(research_files.items()):
    text = Path(fname).read_text()
    add_text_source(research_nb_id, text, title=title)
    time.sleep(1)

# Then query the research NLM for executive synthesis
notebook_query(research_nb_id,
    "What does A bring that B lacks? What does B bring that A lacks? "
    "Top 3 integration opportunities? Should they integrate or compete?")
```

## Hephaestus (Codex) Limitations — Critical

**NEVER delegate to Hephaestus tasks that require MCP tools.**

Hephaestus (gpt-5.3-codex) runs in a sandboxed codex environment with NO access to:
- `mcp__notebooklm__*` tools
- `mcp__exa__*` tools
- `mcp__linear__*` tools
- Any other MCP server tools

**Hephaestus IS good for:** File reading/writing, bash commands, code analysis, Python scripting, generating upload scripts that YOU then execute via MCP.

**Pattern:** Have Hephaestus generate the batch upload script → you execute it and call MCP tools yourself.

## Subprocess Arg Length Limit

The `add_text_source` pipx-venv subprocess approach fails for text > ~90K chars:
```
[Errno 7] Argument list too long
```

**Fix:** Split text to ≤80K chars before calling `add_text_source`. For the skeleton layer docs, split at `## ` boundaries as shown above.

Direct MCP tool calls (`mcp__notebooklm__notebook_add_text`) have no such limit but require reading the file content inline.

## XML Invalid Characters

When running repomix on codebases with terminal control sequences (ANSI escape codes), the XML output may contain invalid characters:

```python
# Strip invalid XML chars before parsing
import re
with open('repomix-output.xml', 'rb') as f:
    data = f.read()
cleaned = re.sub(rb'[\x00-\x08\x0b\x0c\x0e-\x1f]', b'', data)
with open('repomix-output.xml', 'wb') as f:
    f.write(cleaned)
```

## NLM Notebook Naming Convention

```
Forensic Ingest: {Project}-Skeleton ({YYYY-MM-DD})    ← architecture
Forensic Ingest: {Project}-Raw-{N} ({YYYY-MM-DD})     ← code (N=1..15)
{ProjectA}/{ProjectB} Research ({YYYY-MM-DD})          ← comparative research
```

## Querying Strategy

```python
# Architecture question → Skeleton (all sources)
notebook_query(skeleton_id, "How is RBAC structured?")

# Targeted subsystem code → lookup registry, then query specific source
source_id = registry["clusters"]["coderd-rbac"]["raw_sources"][0]["source_id"]
nb_id = registry["clusters"]["coderd-rbac"]["raw_sources"][0]["notebook_id"]
notebook_query(nb_id, "Show RBAC policy evaluation logic", source_ids=[source_id])

# Research/comparison → research notebook
notebook_query(research_id, "What integration opportunities exist?")
```

## References
- Oracle-Cortex forensic_ingest modules: `/home/devuser/Oracle-Cortex/scripts/forensic_ingest/`
- Batch upload script template: `/tmp/forensic-ingest/batch_upload.py`
- coder/coder registry example: `/tmp/forensic-ingest/coder-registry.json`
