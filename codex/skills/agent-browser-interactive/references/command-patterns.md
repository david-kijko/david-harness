# Command Patterns

Use these patterns when the task explicitly wants `agent-browser` and benefits from an interactive, persistent browser loop.

## Bootstrap Once

Run the bundled bootstrap script from the target workspace:

```bash
/home/devuser/.codex/skills/agent-browser-interactive/scripts/bootstrap-agent-browser.sh
```

Use `--upgrade` when the local CLI version is older than the upstream repo you are following:

```bash
/home/devuser/.codex/skills/agent-browser-interactive/scripts/bootstrap-agent-browser.sh --upgrade
```

## Open, Snapshot, Interact

Prefer this sequence for first contact with a page:

```bash
agent-browser open https://example.com
agent-browser wait --load domcontentloaded
agent-browser snapshot -i -C -c
```

Then interact with the fresh refs:

```bash
agent-browser fill @e2 "user@example.com"
agent-browser click @e5
agent-browser wait --load networkidle
agent-browser snapshot -i -C -c
```

### When Chaining Is Safe

Chain commands only when no intermediate output must be interpreted:

```bash
agent-browser open https://example.com \
  && agent-browser wait --load networkidle \
  && agent-browser screenshot --annotate
```

Do not chain through `snapshot` if later steps depend on the refs you have not inspected yet.

## Persistence Choices

### Reuse the Same Running Browser

```bash
agent-browser --session settings-page open https://app.example.com/settings
agent-browser --session settings-page snapshot -i -C -c
```

Use `--session` when you need multiple isolated live browsers at once.

### Persist Auth Across Restarts

```bash
agent-browser --session-name app-login open https://app.example.com/login
```

Use `--session-name` when cookies and localStorage are enough.

### Persist Full Browser State

```bash
agent-browser --profile ./.agent-browser/profile open https://app.example.com
```

Use `--profile` when the site depends on IndexedDB, service workers, extensions, or cache.

### Explicit State Files

```bash
agent-browser state save ./.agent-browser/auth.json
agent-browser state load ./.agent-browser/auth.json
```

Use `state save/load` when you need a portable file you can move, inspect, or delete explicitly.

## Visual + Text Pairing

Use snapshots for structure and annotated screenshots for layout-sensitive reasoning:

```bash
agent-browser snapshot -i -C -c
agent-browser screenshot --annotate
```

After `screenshot --annotate`, the numbered overlay still maps to the same `@eN` refs, so you can reason visually and then click the matching ref without a separate locator hunt.

## Semantic Locators

Use them when the latest snapshot is missing a good ref or when text is more stable than DOM structure:

```bash
agent-browser find role button click --name "Save"
agent-browser find label "Email" fill "user@example.com"
agent-browser find text "Forgot password" click
agent-browser find placeholder "Search" type "playwright"
```

Use `--exact` when fuzzy text would be risky.

## Page Diagnostics

Use these before inventing a theory about what the UI is doing:

```bash
agent-browser console
agent-browser errors
agent-browser network requests --filter api
agent-browser get styles @e4
agent-browser get box @e4
agent-browser get url
agent-browser get title
```

## Diffing

Use diffs when the task is about regression checking, before/after comparisons, or visual drift:

```bash
agent-browser diff snapshot
agent-browser diff screenshot --baseline ./before.png
agent-browser diff url https://staging.example.com https://prod.example.com --selector "#main"
```

Prefer `diff snapshot` for quick structural change detection and `diff screenshot` when layout or rendering is the actual question.

## Downloads

Set the download directory up front when the task expects files:

```bash
agent-browser --download-path ./downloads open https://example.com
agent-browser download @e3 ./downloads/report.csv
agent-browser wait --download ./downloads/report.csv
```

## Data Extraction

Use text mode for human reasoning and JSON mode for downstream parsing:

```bash
agent-browser get text body
agent-browser snapshot -i --json
agent-browser get text @e4 --json
```

If the page is large, reduce output size first:

```bash
agent-browser snapshot -i -C -c -d 4 -s "#main"
agent-browser --max-output 30000 get text body
```

## Existing Chrome or Electron

Use CDP attachment when the browser or desktop app is already running:

```bash
agent-browser --auto-connect snapshot -i -C -c
agent-browser --cdp 9222 snapshot -i -C -c
```

This is the right path for Electron apps that expose a debugging port, or for browser sessions that were launched outside the current command flow.

## Config Files

For repeated work in one repo, prefer a project-level `agent-browser.json` instead of repeating flags:

```json
{
  "headed": true,
  "sessionName": "local-dev",
  "contentBoundaries": true,
  "maxOutput": 50000
}
```

Read [safety-config.md](safety-config.md) before adding allowlists or action policies.
