# Ingest Modes

Pick the lightest ingest mode that still preserves the context needed for later queries.

## Mode 1: Direct Single-Notebook Ingest

Use for small source sets, docs, RFCs, notes, or a modest repo slice.

```bash
NLM=/home/david/.local/bin/nlm
$NLM notebook create "Service Overview"
$NLM alias set svc-overview <notebook-id>
$NLM source add svc-overview --url https://example.com/design --wait
$NLM source add svc-overview --file ./spec.pdf --wait
$NLM source add svc-overview --text "$(cat summary.md)" --title "Working Notes" --wait
```

## Mode 2: Research Then Import

Use when the notebook does not yet have the right sources.

```bash
NLM=/home/david/.local/bin/nlm
$NLM research start "OpenTelemetry collector deployment patterns" --source web --mode fast --title "OTel research"
$NLM research status <task-id>
$NLM research import <task-id> --notebook-id <notebook-id>
```

Verified behavior on Hetzner:

- `research start QUERY`
- `--source web|drive`
- `--mode fast|deep`
- `--notebook-id` for an existing notebook
- `--title` to create a new notebook for imported results

## Mode 3: Manual Repo Ingest

Use when you need deterministic code context and already know what should go into the notebook.

1. Produce a repo dump or curated markdown slices.
2. Split oversized material into smaller topic-focused chunks.
3. Upload each chunk as a titled text source.
4. Add a routing document such as `CODE-MAP-INDEX`.
5. Query with `--source-ids` when precision matters.

```bash
NLM=/home/david/.local/bin/nlm
$NLM notebook create "Repo Skeleton"
$NLM alias set repo-skel <notebook-id>
$NLM source add repo-skel --text "$(cat L1-architecture.md)" --title "L1-Architecture" --wait
$NLM source add repo-skel --text "$(cat CODE-MAP-INDEX.md)" --title "CODE-MAP-INDEX" --wait
```

## Mode 4: Dual-Notebook Large-Codebase Pattern

Use when a repo is too large or too heterogeneous for a single notebook.

Create:

- one skeleton notebook for architecture, subsystem summaries, dependency maps, and routing
- one or more raw-code notebooks for full source chunks grouped by subsystem or layer

Minimum structure:

- `Skeleton`
  - architecture overview
  - layer summaries
  - dependency graph summary
  - `CODE-MAP-INDEX`
- `Raw-N`
  - chunked subsystem sources
  - stable titles so queries can target the right source family

Routing rule:

- architecture questions -> skeleton notebook
- implementation detail questions -> raw notebook for the relevant subsystem
- cross-cutting questions -> query skeleton first, then targeted raw notebooks

## Source Hygiene

- Use canonical titles so later updates replace the right source cleanly
- Prefer subsystem-sized chunks over giant dumps
- Add `--wait` to sources you plan to query immediately
- Keep a notebook alias and, for large ingests, a sidecar registry file outside NotebookLM

## Query After Ingest

```bash
NLM=/home/david/.local/bin/nlm
$NLM notebook query repo-skel "What are the main layers and boundaries?"
$NLM notebook query repo-skel "Which sources should I inspect for auth?" --source-ids <index-source-id>
```
