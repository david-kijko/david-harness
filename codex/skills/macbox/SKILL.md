---
name: macbox
description: Use when the user asks to run or explain basic terminal commands in the macOS sandbox/noVNC environment, needs operational command patterns, or wants safe command-first troubleshooting of containerized macOS sessions.
---

# MacBox

Run this skill for practical terminal operations against the macOS sandbox stack (Docker container + noVNC access).

## What this skill covers

- Basic shell navigation and inspection commands
- Docker lifecycle and health checks for the macOS sandbox container
- noVNC reachability/auth checks
- Clipboard/paste troubleshooting in browser-based noVNC sessions
- Safe defaults for command execution and verification

## Workflow

1. Detect context:
   - If repository contains `macos-intent/`, run commands from that folder.
   - Otherwise, discover target stack with `docker ps` and `docker inspect`.
2. Start with read-only inspection commands first.
3. Apply minimal change commands only when needed.
4. Verify each change with concrete output (`curl`, `docker ps`, exit codes).
5. Report exact commands run and short interpretation.

## Core command patterns

For command recipes and copy/paste snippets, read:
- `references/basic-terminal-commands.md`

For authoring patterns and rationale, read:
- `references/implementation-patterns.md`

For a compact command runner, use:
- `scripts/macbox-cli.sh`

## Guardrails

- Prefer `set -euo pipefail` in multi-step shell scripts.
- Avoid destructive commands unless explicitly requested.
- Keep services local-bound when possible (e.g., `127.0.0.1:8006`).
- When editing runtime config, back up files first.
