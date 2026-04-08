---
name: neo2.0
description: "Next-generation implementation pipeline with browser-verified definition of done. Extends /neo with autonomous agent-browser validation at Review (Step 5) and L3 Browser Gate (Step 7). Every feature is verified against a live deployment URL before completion. Triggers: 'neo2', 'neo 2.0', 'browser verified', 'verify in browser', 'test it live', 'definition of done'. Also triggers on any /neo invocation when the task involves user-facing features, API endpoints, dashboards, forms, or any UI that users interact with."
---

# Neo 2.0 — Browser-Verified Implementation Pipeline

Every feature affects users. Code that passes 428 tests but breaks the login page is not done.

Neo 2.0 extends the Neo pipeline with **autonomous browser validation** via `agent-browser`. Two integration points ensure nothing ships without being verified against a live deployment:

1. **Step 5 Review**: Browser quick-check catches obvious breakage → STEERs Codex if broken
2. **Step 7 L3 Browser Gate**: Full verification with screenshots and evidence → blocks completion if user flows fail

**Requires**: `agent-browser` CLI (installed at `/home/devuser/agent-browser/`), live deployment URL

## Pipeline

```
Task Description
      |
      v
 1. INGEST — forensic-ingest connected repos (reuse existing registries)
      |
      v
 2. ESTIMATE — estimate_difficulty() → EASY / MEDIUM / HARD
      |
      v
 3. RESEARCH — calibrated Perplexity queries (1/3/5) + NotebookLM
      |
      v
 4. EXECUTE — Codex with calibrated reasoning + danger-full-access
      |
      v
 5. REVIEW — Claude checks output + Anti-Sandra scan
      |     + BROWSER QUICK-CHECK ← NEW
      |     agent-browser autonomous loop on critical user flows
      |     If broken → STEER Codex (max 3 attempts)
      |
      v
 6. GATES — L0 plan → L1 phase → L2 commit (hook-enforced)
      |
      v
 7. L3 BROWSER GATE ← NEW
      |     Full browser verification against deployment URL
      |     All inferred user flows tested autonomously
      |     Screenshot evidence captured for each flow
      |     Pass/Fail with detailed findings report
      |
      v
 DONE — Feature verified end-to-end in a real browser
```

## Steps 1-4: Unchanged from Neo

Use the standard Neo pipeline for INGEST, ESTIMATE, RESEARCH, and EXECUTE. See `/neo` skill for details.

```python
from neo2 import estimate_difficulty, build_research_plan, TaskDifficulty, QueryContext
from neo2.ingest import resolve_repo_paths, ingest_repos, build_enriched_research_plan
from neo2.codex import run_codex, create_session, session_next_prompt
```

## Step 5: Review + Browser Quick-Check

After Codex delivers and the Anti-Sandra scan runs, execute a **browser quick-check** before deciding ACCEPT or STEER.

### 5a. Infer the Browser Verification Plan

Analyze git diff + task description to determine what to test:

```bash
# Get the changes Codex made
cd /path/to/project
git diff --name-only HEAD~1        # Changed files
git diff HEAD~1 -- '*.py' '*.ts' '*.tsx' '*.html' '*.vue' '*.svelte'  # Code changes
```

**Inference rules — what changed maps to what to test:**

| Change Pattern | Inferred Browser Test |
|---|---|
| Route/endpoint added or modified (`@app.get`, `router.post`, `app.use`) | Navigate to the endpoint URL, verify response renders |
| Auth middleware changed (`login`, `auth`, `session`, `jwt`) | Test login flow end-to-end, verify protected routes reject/allow |
| Form component modified (`.tsx`, `.vue`, `.svelte` with `<form>`, `<input>`) | Fill and submit the form, verify success/error states |
| API integration changed (fetch, axios, client calls) | Navigate to the UI that calls the API, verify data loads |
| Dashboard/admin panel modified | Navigate to the dashboard, verify widgets/tables render with data |
| Database model changed (migrations, schema) | Navigate to CRUD pages, verify create/read/update/delete works |
| CSS/styling changed | Take screenshot, verify no layout breakage |
| Error handling modified (try/catch, error boundaries) | Trigger error conditions, verify error pages render correctly |
| Navigation/routing changed | Navigate through all affected routes, verify no 404s |

**Build the verification plan mentally:**

1. Read the task description — what was the user trying to achieve?
2. Read the git diff — what files changed and what patterns match?
3. Identify the deployment URL — ask the user if not obvious from context
4. Map changes to user flows — each change pattern produces 1+ flows
5. Prioritize — auth/access flows are **critical**, UI flows are **high**, styling is **normal**

### 5b. Execute Browser Quick-Check (Critical Flows Only)

Run only **critical** flows during review. This is a fast gate — if the app is obviously broken, STEER Codex immediately.

```bash
# 1. Open the deployment URL
agent-browser open https://app.example.com
agent-browser wait --load networkidle

# 2. Snapshot to verify the page loads at all
agent-browser snapshot -i
# If this shows an error page, 500, or blank → STEER immediately

# 3. Screenshot for evidence
agent-browser screenshot /tmp/neo2-evidence/review-initial.png
```

**The Autonomous Agent Loop** — for each critical flow:

```
LOOP (per flow):
  1. agent-browser open {deployment_url}{flow.entry_url}
  2. agent-browser wait --load networkidle
  3. agent-browser snapshot -i
     → Claude reads the snapshot
     → Identifies interactive elements via @refs
     → Decides: does the page match expectations?

  4. For each step in the flow:
     a. Execute the action:
        agent-browser click @eN       # Click buttons/links
        agent-browser fill @eN "val"  # Fill form fields
        agent-browser select @eN "v"  # Select dropdowns
        agent-browser press Enter     # Submit forms

     b. Wait for result:
        agent-browser wait --load networkidle
        # or: agent-browser wait @eN  (wait for specific element)
        # or: agent-browser wait --url "**/expected-path"

     c. Re-snapshot to verify:
        agent-browser snapshot -i
        → Claude evaluates: did the action succeed?
        → Any error messages visible?
        → Did the URL change as expected?

     d. Capture evidence:
        agent-browser screenshot /tmp/neo2-evidence/flow-{name}-step-{n}.png

  5. Evaluate success criteria:
     → All expected elements visible?
     → No error states shown?
     → Correct URL reached?
     → Data displayed correctly?

  6. Verdict: PASS or FAIL with specific findings
```

**Adaptive behavior during the loop:**

- **Element not found**: Scroll down (`agent-browser scroll down 500`), re-snapshot, try again. If still not found after 3 scrolls → FAIL with "Element not found"
- **Unexpected modal/dialog**: `agent-browser snapshot -i` to read it, `agent-browser click @eN` to dismiss if possible
- **Error page (500, 404)**: Immediate FAIL — capture screenshot + page text as evidence
- **Loading spinner stuck**: `agent-browser wait 5000`, re-snapshot. If still loading → FAIL with "Page stuck loading"
- **Redirect to login**: Auth flow is broken → FAIL with "Redirected to login unexpectedly"

### 5c. Review Decision

```python
# After browser quick-check
if any_critical_flow_failed:
    review = ReviewResult(
        verdict=ReviewVerdict.STEER,
        findings=(
            "Browser quick-check FAILED:",
            *browser_findings,  # Specific failures with screenshots
            "Anti-Sandra findings:",
            *anti_sandra_findings,
        ),
        steering_prompt=f"""
        The deployment at {deployment_url} shows these browser failures:
        {browser_failure_summary}

        Fix these issues. The user must be able to:
        {failed_flow_descriptions}
        """,
    )
    # Feed back to Codex for another attempt (max 3 total)
else:
    review = ReviewResult(
        verdict=ReviewVerdict.ACCEPT,
        findings=("All critical browser flows pass", *anti_sandra_findings),
    )
```

## Step 6: Gates (Unchanged)

Standard L0 → L1 → L2 gate execution. See `/neo` skill for details.

```bash
cd /home/devuser/neo1.0
python -m neo2 full-pipeline --plan PLAN.md --phase 01 --commit-message "feat: ..."
```

## Step 7: L3 Browser Gate — Full Verification

After L0/L1/L2 pass, execute **all** inferred user flows (not just critical). This is the final gate before declaring the feature complete.

### 7a. Full Browser Verification

```bash
# Create evidence directory
mkdir -p .neo2-artifacts/browser-verification/

# Session for this verification run
export AGENT_BROWSER_SESSION=neo2-l3-verify
```

**Execute ALL flows** (critical + high + normal priority):

For each flow, run the autonomous agent loop from Step 5b. Additionally:

```bash
# Capture console errors during each flow
agent-browser console error
# → Any JS errors = findings to report

# Capture network failures
agent-browser network requests --filter "status>=400"
# → Any 4xx/5xx requests = findings to report

# Take diff screenshots if baseline exists
agent-browser diff screenshot --baseline .neo2-artifacts/browser-verification/baseline-{flow}.png
# → Visual regression detection
```

### 7b. Evidence Collection

For each flow, capture and store:

```bash
# Screenshots at key moments
agent-browser screenshot .neo2-artifacts/browser-verification/{flow-name}-initial.png
agent-browser screenshot .neo2-artifacts/browser-verification/{flow-name}-final.png
agent-browser screenshot --annotate .neo2-artifacts/browser-verification/{flow-name}-annotated.png

# Full page screenshot for layout verification
agent-browser screenshot --full .neo2-artifacts/browser-verification/{flow-name}-fullpage.png

# Console output
agent-browser console > .neo2-artifacts/browser-verification/{flow-name}-console.txt

# Snapshot diff (before vs after interaction)
agent-browser diff snapshot > .neo2-artifacts/browser-verification/{flow-name}-diff.txt
```

### 7c. L3 Pass/Fail Criteria

| Priority | Result | Gate Decision |
|---|---|---|
| Critical flow fails | Any | **FAIL** — feature is not done |
| High flow fails | Any | **FAIL** — feature is not done |
| Normal flow fails | Any | **WARN** — feature is done with caveats |
| All flows pass | All | **PASS** — feature is verified |

**On FAIL**: Generate a findings report, do NOT declare feature complete. The report includes:
- Which flows failed and why
- Screenshots showing the failure state
- Console errors captured
- Specific elements that were missing or broken
- Suggested fixes

**On PASS**: Generate a verification report confirming all flows work. Include screenshots as evidence.

### 7d. Verification Report

Generate `.neo2-artifacts/browser-verification/REPORT.md`:

```markdown
# Browser Verification Report

## Summary
- **Deployment URL**: https://app.example.com
- **Date**: 2026-03-03
- **Verdict**: PASS / FAIL
- **Flows tested**: N total (N critical, N high, N normal)
- **Passed**: N | **Failed**: N | **Warnings**: N

## Flow Results

### [PASS] Login Flow (Critical)
- Entry: /login
- Steps: Fill email → Fill password → Click submit → Verify dashboard
- Evidence: ![login-final](login-flow-final.png)

### [FAIL] API Dashboard (High)
- Entry: /admin/api-keys
- Steps: Navigate → Verify table renders → Click "Create Key"
- **Failure**: Table shows "No data" despite API returning 200
- **Console Error**: `TypeError: Cannot read property 'map' of undefined`
- Evidence: ![api-dash-fail](api-dashboard-final.png)

## Console Errors
- [ERROR] TypeError: Cannot read property 'map' of undefined (api-dashboard.js:42)

## Recommendations
1. Fix data binding in API dashboard component
2. Add null check for API response before mapping
```

### 7e. Cleanup

```bash
# Close the verification session
agent-browser --session neo2-l3-verify close
```

## agent-browser Command Reference (Quick)

```bash
# Navigation
agent-browser open <url>              # Navigate to URL
agent-browser close                   # Close browser

# Snapshot (ALWAYS use -i for interactive elements)
agent-browser snapshot -i             # Get refs: @e1, @e2, ...
agent-browser snapshot -i -C          # Include cursor-interactive elements
agent-browser snapshot -s "#selector" # Scope to CSS selector

# Interaction (use @refs from snapshot)
agent-browser click @e1               # Click
agent-browser fill @e2 "text"         # Clear + type
agent-browser select @e1 "option"     # Dropdown
agent-browser check @e1               # Checkbox
agent-browser press Enter             # Key press
agent-browser scroll down 500         # Scroll

# Information
agent-browser get text @e1            # Element text
agent-browser get url                 # Current URL
agent-browser get title               # Page title

# Wait
agent-browser wait @e1                # Wait for element
agent-browser wait --load networkidle # Wait for network
agent-browser wait --url "**/path"    # Wait for URL pattern
agent-browser wait 2000               # Wait ms

# Capture
agent-browser screenshot path.png     # Screenshot
agent-browser screenshot --full       # Full page
agent-browser screenshot --annotate   # With element labels

# Diff
agent-browser diff snapshot           # Compare vs last snapshot
agent-browser diff screenshot --baseline before.png  # Visual diff

# Debug
agent-browser console                 # View console logs
agent-browser console error           # View errors only
agent-browser errors                  # JS errors
agent-browser network requests        # View network

# Session
agent-browser --session name open url # Named session
agent-browser session list            # List sessions
```

**Critical rules:**
- Refs (`@e1`, `@e2`) are **invalidated** after navigation. Always re-snapshot after clicks that navigate.
- Use `wait --load networkidle` after `open` for slow pages.
- Chain commands with `&&` when you don't need intermediate output.

## Common Browser Verification Patterns

### Login Flow Verification

```bash
agent-browser open https://app.example.com/login
agent-browser wait --load networkidle
agent-browser snapshot -i
# → Expect: email input (@e1), password input (@e2), submit button (@e3)

agent-browser fill @e1 "test@example.com"
agent-browser fill @e2 "testpassword"
agent-browser click @e3
agent-browser wait --url "**/dashboard"
agent-browser snapshot -i
# → Expect: dashboard content, user greeting, navigation menu
agent-browser screenshot /tmp/neo2-evidence/login-success.png
```

### API Endpoint Accessibility

```bash
agent-browser open https://app.example.com/api/health
agent-browser wait --load networkidle
agent-browser snapshot
# → Expect: JSON response with status: "ok"
# If 401/403 → auth is blocking API access
# If 500 → server error, endpoint is broken

agent-browser get text body
# → Parse the response text to verify correct data
```

### Form Submission + Backend Integration

```bash
agent-browser open https://app.example.com/settings
agent-browser wait --load networkidle
agent-browser snapshot -i
# → Find form fields

agent-browser fill @e1 "Updated Name"
agent-browser click @e5  # Save button
agent-browser wait --load networkidle
agent-browser snapshot -i
# → Expect: success message, updated value shown
# → No error toasts, no red validation borders

# Verify persistence — reload and check
agent-browser reload
agent-browser wait --load networkidle
agent-browser get text @e1
# → Should show "Updated Name" (not reverted to old value)
```

### Dashboard Data Loading

```bash
agent-browser open https://app.example.com/admin/dashboard
agent-browser wait --load networkidle
agent-browser snapshot -i

# Check for data vs empty states
agent-browser get text body
# → If "No data", "Loading...", or empty table → data isn't wiring through
# → If actual data visible → backend integration works

# Check console for API errors
agent-browser console error
# → Any fetch/XHR errors = broken backend integration

agent-browser screenshot --full /tmp/neo2-evidence/dashboard.png
```

### Protected Route Access

```bash
# Without auth — should redirect to login or show 401
agent-browser open https://app.example.com/admin
agent-browser wait --load networkidle
agent-browser get url
# → Expect redirect to /login or 401 page

# With auth — should show admin content
agent-browser state load auth.json  # Pre-saved auth state
agent-browser open https://app.example.com/admin
agent-browser wait --load networkidle
agent-browser snapshot -i
# → Expect: admin panel content, not a login redirect
```

## Integration with Neo Pipeline

### When to use Neo 2.0 vs Neo

| Scenario | Use |
|---|---|
| Pure backend refactoring (no UI impact) | `/neo` (original) |
| Any feature that users interact with | `/neo2.0` |
| API endpoint changes | `/neo2.0` — verify endpoints are accessible |
| Auth/session changes | `/neo2.0` — verify login flow works |
| Database schema changes | `/neo2.0` — verify CRUD operations in UI |
| Frontend component changes | `/neo2.0` — verify rendering + interaction |
| CLI tool changes (no web UI) | `/neo` (original) |

**Rule of thumb**: If a user will eventually see or interact with the change through a browser, use Neo 2.0.

### Deployment URL Discovery

The deployment URL is always available. Common patterns:
- Check project README for deployment URL
- Check `.env` or environment config for `NEXT_PUBLIC_URL`, `VITE_API_URL`, etc.
- Check CI/CD config for deployment targets
- Ask the user: "What's the deployment URL for this project?"

**Store the URL** once discovered for reuse across the session.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Skipping browser verification for "backend-only" changes | Backend changes affect frontend. Test the UI. |
| Using stale refs after navigation | Always `snapshot -i` after any click that navigates |
| Not waiting for network idle | `wait --load networkidle` after every `open` or form submit |
| Testing only the happy path | Also test error states, empty states, auth rejection |
| Not capturing evidence screenshots | Every flow needs screenshots in `.neo2-artifacts/` |
| Declaring done without L3 pass | If L3 fails, the feature is NOT done |
| Running all flows during Step 5 review | Step 5 = critical only. Step 7 = all flows. |
| Not checking console errors | JS errors in console = broken integration even if UI looks OK |
| Forgetting to close browser session | Always `agent-browser close` when done |
