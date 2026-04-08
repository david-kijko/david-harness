---
name: nlm
description: "Use when working with Google NotebookLM through the nlm CLI"
---

# NLM

## Overview

Use this skill as the single entrypoint for NotebookLM work on this machine.

This skill is **utility-first**. Normal notebook work can use the `nlm` CLI, but auth truth lives in the local bridge utility running on David's laptop, not in ad hoc cookie edits on Hetzner.

## When to Use

Use this skill when the user wants to:

- create, inspect, rename, or delete notebooks
- add text, URL, Drive, or file sources
- query existing notebooks or compare across notebooks
- generate NotebookLM studio assets
- ingest a codebase into NotebookLM
- choose between small-repo ingest and large-repo dual-notebook ingest
- refresh auth, diagnose failures, or recover from stale sessions

Do not use this skill for generic web research that does not need NotebookLM.

## First Checks

Always start with:

```bash
NLM=/home/david/.local/bin/nlm
$NLM login --check
```

If auth is suspect, do not mutate cookies first. Read `references/troubleshooting.md` and follow the recovery order there.

Then decide the mode:

| Need | Go to |
|---|---|
| Existing notebook operations | `references/cli-surfaces.md` |
| Studio outputs and assets | `references/assets.md` |
| New-source research or codebase ingest | `references/ingest-modes.md` |
| Auth/rate-limit/source-readiness issues | `references/troubleshooting.md` |

## Core Rules

- The laptop tray utility and `notebooklm-cookie-refresh.service` are the source of truth for NotebookLM auth.
- `hetzner-dev` only carries a mirrored `/home/david/.notebooklm-mcp/auth.json`; treat it as disposable state.
- If the current agent already has NotebookLM MCP tools configured, a successful `notebook_list` or equivalent sanity check means the bridge utility is healthy; do not touch auth.
- Prefer aliases for frequently used notebooks.
- Use `--wait` when adding sources that must be queryable immediately after upload.
- For destructive actions, require explicit confirmation.
- For codebase ingest, pick the ingest mode before uploading anything.
- For large repos, avoid naive single-notebook dumps.
- Do not use `save_auth_tokens`, manual `auth.json` edits, or repeated `nlm login` attempts as first-line repair on Hetzner.

## Fast Path

```bash
NLM=/home/david/.local/bin/nlm
$NLM login --check
$NLM notebook list
$NLM alias list
```

From there:

- Existing notebook: inspect/query it directly.
- New material: create notebook, add sources, then query.
- Codebase: use the ingest decision tree in `references/ingest-modes.md`.
