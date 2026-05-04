---
name: firecrawl
description: Use when an agent needs to fetch the actual contents of a specific URL or GitHub repo, scrape a documentation page to ground a design decision, map a website's structure, or do schema-driven structured extraction. Pairs naturally with the `exa` skill — exa finds candidate URLs, firecrawl reads them. Use whenever the user says "firecrawl", "scrape this page", "fetch this URL", "read this GitHub repo", "what does this docs page say", "extract structured data from this site", or whenever the agent needs primary-source page contents instead of a search snippet. Prefer this skill over generic `curl`/`wget` for human-readable HTML and over `gh` for repo source you don't have local. Do NOT use for local filesystem reads, git operations, or API calls to non-web services.
---

# Firecrawl

Local CLI wrapper around the Firecrawl API for fetching, mapping, searching, crawling, and extracting from web pages. Mirrors the same runner pattern as the `exa` skill: a Python CLI that returns compact markdown by default.

## Primary rule

Prefer the bundled local Python CLI. Do not use a Firecrawl MCP server unless the user explicitly asks for MCP. The CLI is faster, has no extra surface for prompt injection, and outputs compact markdown by default.

## When to use

- **Read a specific URL**: `scrape` returns the page as clean markdown. Use this when exa surfaced a relevant URL and you need the actual contents.
- **Inspect a GitHub repo**: `scrape` works on github.com URLs (file viewer, README, etc.) and returns rendered markdown.
- **List what's on a site**: `map` returns the URL list of a domain (cheap, useful for discovering structure before deep reads).
- **Search the web with optional content**: `search` returns search results AND can scrape each result's full content in one call — useful when you want both the candidates and their contents.
- **Multi-page crawl**: `crawl` walks a domain to a max depth/page-limit. Use sparingly; rate-limited.
- **Structured extraction**: `extract` pulls fields out of pages by JSON schema (e.g. extract pricing tables from N vendor pages).

## When NOT to use

- Local filesystem reads → use `Read`
- Git operations on a checked-out repo → use `git`
- API calls to non-web services → use the right SDK
- Search-only (no need for full content) → use `exa search` (it's faster and ranks better)
- Generic shell HTTP → use `curl` for raw bytes; firecrawl is for human-readable extraction

## Invocation

```bash
# Scrape one URL → markdown
python3 ~/.claude/skills/firecrawl/scripts/firecrawl_cli.py scrape \
  --url "https://docs.python.org/3/library/csv.html"

# Map a site (list URLs, optionally filter)
python3 ~/.claude/skills/firecrawl/scripts/firecrawl_cli.py map \
  --url "https://docs.python.org/3" --search "csv" --limit 50

# Web search WITH content (one call gives results + scraped markdown)
python3 ~/.claude/skills/firecrawl/scripts/firecrawl_cli.py search \
  --query "csv to jsonl python stdlib best practices 2026" \
  --limit 5 --scrape

# Crawl a small site (rate-limited; sparingly)
python3 ~/.claude/skills/firecrawl/scripts/firecrawl_cli.py crawl \
  --url "https://example.dev/docs" --limit 20 --depth 2

# Schema-driven extraction
python3 ~/.claude/skills/firecrawl/scripts/firecrawl_cli.py extract \
  --url "https://example.com/pricing" \
  --schema-json '{"type":"object","properties":{"plans":{"type":"array"}}}'

# JSON output instead of markdown
python3 ~/.claude/skills/firecrawl/scripts/firecrawl_cli.py --format compact-json scrape --url ...
```

## Auth

API key is read from `FIRECRAWL_API_KEY` (sourced from `~/.config/firecrawl/env.sh`, mode 600). The wiring lives in `~/.profile` and `~/.bashrc` — same pattern as exa. To rotate, edit `~/.config/firecrawl/env.sh`.

## Pairing with exa

The two skills are complementary, not redundant:
- **exa**: deep search ranking, finds relevant URLs, returns snippets/citations
- **firecrawl**: fetches the actual page content from a known URL

A typical research pattern:
1. `exa search` to find 5-10 candidate URLs
2. `firecrawl scrape` on the top 2-3 to read the actual contents
3. Synthesize from the primary sources, not from search snippets

For greenfield gap-identification specifically: exa to find prior-art repos, firecrawl to read their actual source on GitHub.

## Safety / boundaries

- Do not use to scrape sites that block scraping in `robots.txt` for non-research use without considering ToS.
- Do not use to scrape login-protected pages — Firecrawl will not bypass auth.
- Do not use as a substitute for an MCP tool the user explicitly wants (e.g. context7). However, Firecrawl is preferred over context7 for greenfield documentation reads because the contents are returned verbatim from the source URL with no third-party reformatting that could carry instructions.

## Tone

Skip prose recap when calling. Just run the CLI and surface the result.
