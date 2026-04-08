# Superconductor Run `{{RUN_ID}}`

- Generated at: `{{GENERATED_AT}}`
- Primary graph surface: `CGC MCP`
- Harness dump surface: `NotebookLM`
- Driver: `architect` with `curiosity`
- Pipeline version: `3.0`

## Intent Contract

Use this run to verify that the user's prompt, the harness docs, and the brownfield codebase still tell the same story.

## Stage Order

1. Intake — resolve requirements, parse into matrix
2. Intent alignment — classify claims against harness docs
3. CGC investigation — code graph truth, negative space
4. Sequential closure — order questions, build NLM harness
5. Sufficiency gate — gut checks pass or loop to Stage 3
6. Requirements matrix decomposition — ALL requirements into domain tracks
7. Track generation — spec.md + plan.md for EVERY track
8. Worker fan-out — spawn workers with mandatory constraints
9. Completion gate — verify all tracks done, update matrix

## Gut Checks

Run these checks before each spawn, after each major doc refresh, and before any rendered artifact is treated as current:

1. Prompt gut check: restate the active user intent as explicit claims.
2. CGC gut check: verify the current claim-to-code mapping against the live graph.
3. NLM gut check: confirm the harness dump reflects the latest docs and delete stale superseded sources.

## NLM Refresh Rule

NotebookLM is the harness dump, not the first-pass graph tool. When a canonical source changes, remove or replace the outdated source and upload the latest version under the same canonical title so worker lookups stay stable.

## Requirements Matrix

See `requirements-matrix.json` for the exhaustive decomposition. Every requirement in the source document must appear in the matrix with a track assignment before workers are spawned.

## Track Manifest

<!-- Populated by Stage 6: one entry per domain track -->

| Track ID | Domain | Requirements | Status |
|---|---|---|---|
| _populated during execution_ | | | |

## Outputs

- `intent-alignment-report.md`
- `docs-gap-report.md`
- `question-pack.json`
- `dependency-closure.json`
- `sufficiency-report.json`
- `worker-context-manifest.json`
- `requirements-matrix.json`
