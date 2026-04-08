---
name: agent-browser-interactive
description: Use when the user explicitly wants `agent-browser`, asks for persistent or iterative browser automation, needs browser QA with repeated interactions, or wants interactive browser debugging/scraping through the `agent-browser` CLI instead of raw Playwright code.
allowed-tools: Bash(agent-browser:*), Bash(npx agent-browser:*), Bash(npm install -g agent-browser:*)
---

# Agent Browser Interactive

Use `agent-browser` like the proven `playwright-interactive` workflow: keep one browser session alive, build explicit QA coverage before signoff, re-snapshot after every meaningful DOM change, and capture evidence for both functional and visual claims.

## Preconditions

1. Run `scripts/bootstrap-agent-browser.sh` from the target workspace before browser work starts.
2. Work from the repo or project directory that owns the app under test.
3. Treat `agent-browser close` as end-of-task cleanup, not something to do between normal interaction bursts.
4. If the task can expose credentials or hit destructive UI, read [references/safety-config.md](references/safety-config.md) before opening the target page.

## Core Workflow

1. Build a QA inventory before testing.
   - Include user requirements, visible behaviors you intend to verify, and the claims you expect to make in the final response.
   - Convert subjective visual expectations into observable checks.
   - Add at least 2 off-happy-path scenarios.
2. Choose the session model before opening the page.
   - Same live browser, same task: default session or `--session <name>`
   - Persist cookies and localStorage across restarts: `--session-name <name>`
   - Persist richer browser state such as IndexedDB, service workers, or cache: `--profile <dir>`
   - Attach to existing Chrome or Electron: `--auto-connect` or `--cdp <port>`
3. Open the target and take the first compact interactive snapshot.
   - `agent-browser open <url>`
   - `agent-browser wait --load domcontentloaded`
   - `agent-browser snapshot -i -C -c`
4. Interact in short bursts.
   - Use refs from the latest snapshot when possible.
   - Re-snapshot after navigation, modal open/close, content refresh, form submit, or any interaction that might invalidate refs.
   - Use semantic locators only when refs are unavailable or noisy.
5. Run functional QA and visual QA as separate passes.
6. Capture evidence for every signoff claim.
7. Close or intentionally preserve the session only after the task is truly done.

## Default Posture

- Prefer `snapshot -i -C -c` for interactive work. It keeps output small while still catching custom clickable elements.
- Prefer plain-text output while reasoning interactively. Use `--json` only when a later command or script must parse the result.
- Prefer command chaining only when you do not need intermediate output. Do not chain across a `snapshot` whose refs you still need to inspect.
- Prefer `screenshot --annotate` when visual layout, unlabeled icon buttons, or stateful controls matter.
- Prefer `--session-name` for login reuse, `state save/load` for explicit portable state files, and `--profile` when the site depends on richer browser persistence.
- Prefer `console`, `errors`, `network requests`, `get styles`, `get box`, and `diff` to resolve uncertainty instead of guessing.

## Interaction Rules

### Refs First

- Fresh snapshot available: use `@eN`
- Snapshot feels stale: refresh it before touching the page
- Text or labels are stable but refs are noisy: use `find role`, `find label`, `find text`, or `find placeholder`
- Visual element is ambiguous: use `screenshot --annotate`, optionally `highlight`, then reuse those refs

### Reload vs Reset

- Same page, same storage, same task: `agent-browser reload`
- Need a clean browser while keeping saved auth: `agent-browser close`, then reopen with the same `--session-name`
- Need a truly fresh state: switch to a new `--session`
- Need side-by-side comparisons: use separate named `--session` values

## Recovery Rules

- Wrong or stale refs: run `agent-browser snapshot -i -C -c` again
- Page navigated or switched tabs: confirm `agent-browser get url`, then re-snapshot
- Auth vanished after restart: move from ephemeral session to `--session-name` or `--profile`
- Output is too noisy: add `-c`, `-d`, `-s`, `--max-output`, or `--json`
- Unsafe target or sensitive workflow: enable content boundaries, allowed domains, and action policy before continuing
- Browser state feels corrupted: `agent-browser close`, then reopen using the persistence model you actually want

## Read Next When Needed

- [references/command-patterns.md](references/command-patterns.md)
  Use for optimized command recipes, persistence choices, CDP/Electron attachment, data extraction, downloads, and diffing.
- [references/interactive-qa.md](references/interactive-qa.md)
  Use for QA inventory, functional pass rules, visual pass rules, and signoff coverage.
- [references/safety-config.md](references/safety-config.md)
  Use for project config, content boundaries, domain allowlists, action policies, auth vault, and sane defaults.

## Verification Expectations

Before claiming success:

- Confirm the exact flows and claims from the QA inventory were exercised.
- Say which session or persistence mode was used.
- Keep at least one screenshot or annotated capture for each important visual claim.
- Check `console` and `errors` for UI changes, navigation work, or flaky behavior.
- Close the browser or state clearly why the session remains open.
