# Troubleshooting

## Auth Model

- The source of truth is the laptop utility: GTK tray `nlm-mcp-bridge` plus `notebooklm-cookie-refresh.service`.
- Fresh auth is written locally to `~/.notebooklm-mcp/auth.json`.
- The tray pushes that file to `hetzner-dev:/home/david/.notebooklm-mcp/auth.json` on startup, reconnect, and drift.
- `hetzner-dev` is a mirror, not the authority. Manual edits on Hetzner can be overwritten by the next sync.

## First Checks

Start with:

```bash
NLM=/home/david/.local/bin/nlm
$NLM login --check
$NLM doctor
stat -c '%y %s %n' /home/david/.notebooklm-mcp/auth.json
```

If the current agent has NotebookLM MCP tools configured, run a cheap notebook sanity check before touching auth. If that succeeds, the bridge utility is healthy enough for work and you should not mutate auth state.

## Never First-Line Repair

- `save_auth_tokens`
- manual edits to `~/.notebooklm-mcp/auth.json`
- repeated `nlm login` or `nlm login --clear`
- copying partial cookie sets into the server

These steps create bad intermediate states and are not how this system stays healthy.

## Auth Recovery Order

1. Check whether the failure is CLI-only, MCP-only, or both.
2. If MCP works, stop. Use the MCP route and leave auth alone.
3. If Hetzner CLI fails, inspect `auth.json` freshness before assuming Google rejected the cookies.
4. If both Hetzner CLI and MCP fail, assume parity drift or an expired browser session on the laptop utility first, not a server-side cookie formatting problem.
5. Retry only after the laptop utility has had a chance to refresh and re-push auth.
6. Only use interactive `nlm login` when the operator explicitly wants a real re-authentication on the source laptop.

## Real-Time Hetzner Rule

When you are on `hetzner-dev`, do not invent a second auth workflow. Your job is to verify whether the mirrored auth is fresh and whether the bridge utility still answers NotebookLM requests. If not, escalate to the laptop utility path rather than rewriting tokens on the server.

## Common Problems

| Problem | Action |
|---|---|
| CLI auth fails on Hetzner | Check `auth.json` freshness and MCP health before doing anything else |
| MCP works but CLI fails | Use MCP for the task; do not rewrite auth |
| Both CLI and MCP fail | Treat it as bridge parity or source-session failure first |
| Rate limited | Slow down and reduce repeated queries |
| Source not ready | Re-run with `--wait` or inspect source status |
| Upload too large | Chunk the source before upload |
| Notebook answers are weak | Fix source set, titles, and routing/index sources |
| Large repo got messy | Switch to dual-notebook ingest |

## Recovery Rules

- Do not keep retrying a broken auth flow blindly.
- Do not treat Hetzner as the source of truth for NotebookLM auth.
- Do not ask NotebookLM questions before the source set is ready.
- Do not treat a missing answer as permission to hallucinate codebase facts.
- If ingest mode was chosen incorrectly, stop and restructure the notebook instead of piling on more sources.
