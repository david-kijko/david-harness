# Docs Gap Report `{{RUN_ID}}`

- Generated at: `{{GENERATED_AT}}`

## Gap Classes

| Gap Class | Requirement | Evidence | Impact | Required Update |
|---|---|---|---|---|
| `intent-doc drift` | R-XXX | _Prompt intent differs from harness docs_ | `high|medium|low` | _Update doc or refine scope_ |
| `doc-code drift` | R-XXX | _Harness docs differ from implementation_ | `high|medium|low` | _Refresh harness source and NLM dump_ |
| `missing documentation` | R-XXX | _Code path exists without harness coverage_ | `high|medium|low` | _Add or extend docs_ |
| `undocumented implementation` | R-XXX | _Behavior exists but is not described anywhere_ | `high|medium|low` | _Document and gut check intent_ |

## Structural Improvements

- Add diagrams when the current harness path is hard to follow.
- Delete outdated NLM sources after replacement so stale context is not queryable.
