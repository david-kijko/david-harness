# Interactive QA

Use this file when the task is not just "click this once," but requires evidence-backed browser verification.

## QA Inventory

Before testing, create a shared coverage list from:

- The user request
- The user-visible behaviors you implemented or changed
- The claims you expect to make in the final response

Every meaningful claim should map to:

- A functional check
- A visual check in the state where the claim matters
- Evidence you expect to capture

Add at least 2 off-happy-path scenarios that could expose brittle behavior.

## Session Loop

1. Start or reuse the browser session.
2. Open the target or reload it.
3. Take a compact interactive snapshot.
4. Exercise the next item from the QA inventory.
5. Re-snapshot after any interaction that can change refs.
6. Capture screenshot evidence only after the UI is in the exact state being evaluated.
7. Repeat until every item in the QA inventory is covered.

## Functional QA

- Use real user inputs: click, type, fill, check, select, scroll, keyboard, tabs, downloads.
- Verify at least one end-to-end critical flow.
- Confirm the visible outcome, not only an internal assumption.
- Cover obvious controls, toggles, and state changes instead of only the main happy path.
- For reversible controls, test the full cycle: initial state, changed state, return state.
- After the scripted path passes, do a short exploratory pass instead of stopping at the intended path.
- If exploratory testing reveals a new visible state or claim, add it to the QA inventory and cover it.

## Visual QA

- Treat visual QA as separate from functional QA.
- Restate the visible claims and inspect them explicitly.
- Inspect the initial viewport before scrolling away.
- Use `screenshot --annotate` when layout, unlabeled controls, or placement matters.
- Inspect at least one meaningful post-interaction state, not only the landing state.
- If a task supports smaller screens or constrained panels, inspect one realistic smaller size explicitly.
- Look for clipping, overflow, illegible text, weak contrast, broken spacing, visual instability, and mismatched overlays.
- If the UI relies on motion or transitions, inspect a settled state after motion and note whether the transition itself behaved correctly.

## Suggested Evidence

For important browser tasks, keep at least:

- One annotated screenshot for the primary interaction surface
- One screenshot or PDF for the final or saved result, if that result matters
- One console/error check after the main flow
- One URL or title check when navigation is part of the claim

## Negative Checks

Before signoff, ask:

- What visible part of the interface have I not inspected?
- Which control or state in my inventory still lacks evidence?
- What embarrassing defect would the user notice first if they looked closely?

## Signoff Checklist

Do not claim the task is complete until all of these are true:

- The functional path passed with real inputs.
- Coverage was explicit against the QA inventory.
- Each important visible claim has matching evidence.
- Navigation-dependent claims were checked against URL, title, or on-page content.
- Console and error output were checked when relevant.
- You either closed the browser or intentionally kept the session alive and said so.
