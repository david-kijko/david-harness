---
name: launch-app-server-agents
description: >
  Use when launching or verifying Codex app-server-backed agent sessions on the
  Hetzner server, especially over SSH with PTYs, loopback websocket listeners,
  noisy terminal output, remote skill checks, or session-artifact verification.
---

# Launch App Server Agents

Use this skill for Codex app-server work on the Hetzner server.

## Operator Rules

- Observe first: check the target port before starting a listener
- Bind temporary app-server listeners to `127.0.0.1`, not a public interface
- Use `ssh -tt` for remote interactive client sessions
- Prefer `codex --remote ws://127.0.0.1:<port> --no-alt-screen` for remote clients
- Do not trust terminal output alone for verification; confirm through session artifacts
- Clean up temporary listeners and clients, then confirm the port is no longer listening

## Route By Intent

- Launch or connect to a temporary listener: read `references/launch-and-cleanup.md`
- Verify skill discovery or final app-server answers: read `references/session-verification.md`

## Quick Start

```bash
ssh -i /home/david/.ssh/kijko_deploy_key -o BatchMode=yes root@157.90.215.60 \
  'ss -ltnp | grep 48765 || true'

ssh -tt -i /home/david/.ssh/kijko_deploy_key -o BatchMode=yes root@157.90.215.60 \
  'sudo -u david bash -lc "codex app-server --listen ws://127.0.0.1:48765"'
```

## Known Learnings From This Host

- Invalid `SKILL.md` YAML causes silent skill skipping in Codex until you inspect the session or logs
- The remote TUI is noisy and can hide the answer; the session JSONL under `~/.codex/sessions/` is the clean source of truth
- Codex may show an update prompt before the actual session content
- The app-server-backed session may report `cwd` as `/root`; verify actual behavior in the session artifact instead of trusting the banner
