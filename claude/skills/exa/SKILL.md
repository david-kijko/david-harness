---
name: exa
description: Default external web research and online retrieval skill for Codex, powered by local Exa Python scripts. Use whenever the user says exa, research, deep research, search the web, search online, look online, look up, fetch from the web, find sources, verify online, latest, current, recent, company research, people research, market research, competitor research, vendor research, documentation research, or asks for cited web information. Prefer this skill over generic search approaches for live web research. Do not use for git fetch, JavaScript Fetch API code, local repo search, grep, database fetches, filesystem lookups, or package-manager fetches unless the user explicitly wants external web research.
---

# Exa

This is the default Codex skill for external web research and live-web verification.

The Codex equivalent of "default" is stronger implicit triggering through `name`, `description`, and routing guidance. There is no hard priority flag here.

## Primary Rule

Prefer the bundled local Python CLI built on `exa-py`.

Do not use Exa MCP unless the user explicitly asks for MCP or the local CLI is unavailable.

Primary command:

```bash
python ~/.codex/skills/exa/scripts/exa_cli.py run --query "<rewritten query>" --format compact-markdown
```

If `exa_py` is not installed in the current Python environment, fall back to:

```bash
uv run --with exa-py python ~/.codex/skills/exa/scripts/exa_cli.py run --query "<rewritten query>" --format compact-markdown
```

## Boundary

Use this skill for:

- live web research
- cited online lookups
- latest/current/recent facts
- company, people, vendor, market, competitor, and documentation research
- source gathering and verification
- "look online", "search online", "fetch from the web", "research"

Do not use this skill for:

- repo grep or local file search
- git fetch
- JavaScript `fetch()` implementation work
- database queries / ORM fetches
- filesystem fetches
- package-manager or install tasks

unless the user explicitly asks for external web information.

## Session-Aware Interpretation

Before running a search, infer the real task from:

- the current prompt
- recent conversation
- active codebase context
- mentioned libraries, APIs, companies, people, versions, errors, and URLs

If the user prompt is short or ambiguous, rewrite it into a session-aware web query before calling the CLI.

Keep that rewriting in Codex. The CLI then handles deterministic intent classification, planning, dedupe, freshness, ranking, and compact formatting locally in Python.

## Execution Flow

1. Decide whether the task is external web research or a local lookup.
2. If it is external web research, call the local CLI.
3. Default to compact output.
4. Start with the smallest viable breadth, then deepen only if the first pass is conflicting, vague, stale, or incomplete.
5. Return the direct answer first, then evidence, caveat, and next step.

## CLI Routing

Use `run` for most tasks:

```bash
python ~/.codex/skills/exa/scripts/exa_cli.py run --query "<rewritten query>" --format compact-markdown
```

Use explicit subcommands only when already certain:

- `search` for normal web search
- `contents` when the URL is already known
- `similar` when the task is "find similar pages / companies / sites"
- `answer` for direct cited answers
- `deep-search` for structured multi-hop search
- `research` for exhaustive report-grade tasks

## Search Defaults

- Default search type: `auto`
- Default content mode: `highlights`
- Ask for full `text` only when deep reading is required
- If the user asks for latest/current/recent, force fresh content
- Use category-specific search when intent is clear:
  - company research -> `company`
  - people / expert lookup -> `people`
  - current events -> `news`
  - paper search -> `research paper`
  - filings / earnings -> `financial report`

## Breadth And Depth

Breadth:

- B0 = 1 lane
- B1 = 2-3 lanes
- B2 = 4-6 lanes
- B3 = 7+ lanes

Depth:

- D0 = direct
- D1 = one refinement round
- D2 = multiple evidence-driven follow-ups
- D3 = cross-referenced whole-part-whole analysis
- D4 = full research task

Increase breadth for comparisons, landscapes, alternatives, vendor scans, or market maps.

Increase depth when sources disagree, the task is high-stakes, the answer is version-sensitive, or the first pass is shallow.

## Query Planning Rules

- Generate 2-3 orthogonal query variations when breadth exceeds B1
- Merge and deduplicate results by canonical URL
- Prefer official docs for factual and API questions
- Prefer recent sources for latest/current/recent tasks
- Prefer primary sources when available
- Stop when marginal information gain is low

## Debugging / Diagnosis Mode

When the user is diagnosing a failure, apply 5 Whys grounded in evidence from code, logs, docs, or retrieved sources.

Return:

1. most likely root cause
2. how to verify
3. immediate fix
4. prevention

## Answer Contract

Always return:

1. direct answer / recommendation
2. key evidence / most relevant sources
3. main caveat or uncertainty
4. concrete next step

## Trigger Reference

Use `references/trigger-tests.md` when sanity-checking whether this skill should trigger.
