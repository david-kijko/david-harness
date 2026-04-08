# Safety and Config

Use this file when the target page is sensitive, destructive, noisy, or likely to persist state across runs.

## Project-Level Config

Create `agent-browser.json` in the working directory when you need stable defaults for repeated commands:

```json
{
  "headed": true,
  "sessionName": "local-dev",
  "contentBoundaries": true,
  "maxOutput": 50000
}
```

Resolution order is:

1. `~/.agent-browser/config.json`
2. `./agent-browser.json`
3. `AGENT_BROWSER_*` environment variables
4. CLI flags

Use project config for defaults that should follow the repo. Use CLI flags for one-off overrides.

## Safe Defaults for Agent Work

For LLM-driven browsing, prefer these defaults unless the task needs something else:

```json
{
  "contentBoundaries": true,
  "maxOutput": 50000,
  "headed": true
}
```

Add `allowedDomains` and `actionPolicy` whenever the session could hit sensitive or destructive surfaces.

## Domain Allowlist

Restrict navigation and subresource access when you know the allowed targets:

```json
{
  "allowedDomains": [
    "app.example.com",
    "*.app.example.com",
    "cdn.example.com"
  ]
}
```

Equivalent CLI form:

```bash
agent-browser --allowed-domains "app.example.com,*.app.example.com,cdn.example.com" open https://app.example.com
```

Remember to include CDN or auth-provider domains the page actually needs.

## Action Policy

Use an action policy when the browser can reach production, billing, admin, or other destructive UI.

Example restrictive policy:

```json
{
  "default": "deny",
  "allow": ["navigate", "snapshot", "click", "fill", "wait", "get", "scroll"]
}
```

Example policy that keeps normal browsing open but blocks high-risk actions:

```json
{
  "default": "allow",
  "deny": ["eval", "download", "upload"]
}
```

Use it with:

```bash
agent-browser --action-policy ./policy.json open https://app.example.com
```

## Confirmation Gates

Require confirmation for risky categories when the task should pause instead of acting automatically:

```bash
agent-browser --confirm-actions eval,download --confirm-interactive eval "document.title"
```

Use this only when a TTY is available. Non-interactive runs auto-deny.

## Auth Vault

Prefer the built-in auth vault over typing passwords into command history:

```bash
echo "pass" | agent-browser auth save github \
  --url https://github.com/login \
  --username user \
  --password-stdin

agent-browser auth login github
```

The auth vault keeps credentials out of model context and out of most shell history paths.

## Persistence Choices

- `--session-name`: good default for cookies and localStorage across restarts
- `--profile`: use when the app depends on IndexedDB, cache, extensions, or service workers
- `state save/load`: use when you want an explicit state artifact you can move or delete

Do not commit state files or profile directories.

## Output Flooding

Use output caps or scoped snapshots before dumping large pages into the terminal:

```bash
agent-browser --max-output 30000 get text body
agent-browser snapshot -i -C -c -d 4 -s "#main"
```

## Recommended Setup Sequence

For a sensitive browser task:

1. Write `agent-browser.json` with `contentBoundaries`, `maxOutput`, and `headed`
2. Add `allowedDomains` if the target domain set is known
3. Add an `actionPolicy` if destructive UI is in scope
4. Use `--session-name` or `--profile` deliberately, not by accident
5. Only then open the target page
