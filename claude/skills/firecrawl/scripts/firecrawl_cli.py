#!/usr/bin/env python3
"""Firecrawl local CLI — same pattern as exa_cli.py.

Subcommands:
    scrape   Fetch one URL, return markdown (and optional metadata).
    map      Get a sitemap-style list of URLs under a domain.
    search   Web search via Firecrawl, optionally with content scraping.
    crawl    Multi-page crawl of a domain (rate-limited; use sparingly).
    extract  Structured-data extraction with JSON schema.

Default output: compact markdown. Pass --format compact-json for JSON.

API key resolved from FIRECRAWL_API_KEY env var (set by ~/.config/firecrawl/env.sh).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
from typing import Any


def load_api_key() -> str:
    key = os.environ.get("FIRECRAWL_API_KEY", "").strip()
    if not key:
        print(
            "Missing FIRECRAWL_API_KEY. Source ~/.config/firecrawl/env.sh or export it manually.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    return key


def make_client():
    try:
        from firecrawl import Firecrawl
    except ImportError:
        print(
            "firecrawl-py not installed. `pip3 install --user firecrawl-py` or run via uv.",
            file=sys.stderr,
        )
        raise SystemExit(5)
    return Firecrawl(api_key=load_api_key())


def to_dict(obj: Any) -> dict:
    """Best-effort convert pydantic model / dict / arbitrary object to plain dict."""
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        return obj.model_dump(exclude_none=True)
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in vars(obj).items() if not k.startswith("_")}
    return {"value": obj}


# ---------- subcommand handlers ----------

def cmd_scrape(args, fc) -> dict:
    formats = args.format_set or ["markdown"]
    only_main = not args.full_page
    res = fc.scrape(
        args.url,
        formats=formats,
        only_main_content=only_main,
        wait_for=args.wait_ms,
    )
    out = {
        "url": args.url,
        "markdown": getattr(res, "markdown", None),
        "html": getattr(res, "html", None),
        "links": getattr(res, "links", None),
        "metadata": to_dict(getattr(res, "metadata", None)),
    }
    return {k: v for k, v in out.items() if v is not None and v != {}}


def cmd_map(args, fc) -> dict:
    res = fc.map(args.url, search=args.search, limit=args.limit)
    urls = getattr(res, "links", None) or getattr(res, "urls", None) or res
    if hasattr(urls, "model_dump"):
        urls = urls.model_dump()
    return {"url": args.url, "search": args.search, "links": urls}


def cmd_search(args, fc) -> dict:
    formats = args.format_set or (["markdown"] if args.scrape else None)
    kwargs: dict[str, Any] = {"limit": args.limit}
    if formats:
        kwargs["scrape_options"] = {"formats": formats, "only_main_content": True}
    res = fc.search(args.query, **kwargs)
    web = getattr(res, "web", None) or getattr(res, "data", None) or res
    if hasattr(web, "model_dump"):
        web = web.model_dump()
    if isinstance(web, list):
        web = [to_dict(item) for item in web]
    return {"query": args.query, "results": web}


def cmd_crawl(args, fc) -> dict:
    formats = args.format_set or ["markdown"]
    res = fc.crawl(
        args.url,
        limit=args.limit,
        max_depth=args.depth,
        scrape_options={"formats": formats, "only_main_content": True},
    )
    pages = getattr(res, "data", None) or res
    if hasattr(pages, "model_dump"):
        pages = pages.model_dump()
    if isinstance(pages, list):
        pages = [to_dict(p) for p in pages]
    return {"url": args.url, "pages": pages}


def cmd_extract(args, fc) -> dict:
    schema = None
    if args.schema_file:
        schema = json.loads(open(args.schema_file).read())
    elif args.schema_json:
        schema = json.loads(args.schema_json)
    if schema is None:
        raise SystemExit("extract requires --schema-file or --schema-json")
    res = fc.extract(urls=[args.url], schema=schema, prompt=args.prompt)
    data = getattr(res, "data", None) or res
    return {"url": args.url, "data": to_dict(data)}


# ---------- formatting ----------

def format_compact_markdown(cmd: str, payload: dict) -> str:
    out = []
    if cmd == "scrape":
        meta = payload.get("metadata", {})
        out.append(f"# {meta.get('title') or payload.get('url')}")
        if meta.get("description"):
            out.append(f"_{meta['description']}_")
        if meta.get("url"):
            out.append(f"\nSource: {meta['url']}")
        out.append("\n---\n")
        out.append(payload.get("markdown", "(no markdown returned)"))
    elif cmd == "map":
        out.append(f"# Map: {payload['url']}")
        if payload.get("search"):
            out.append(f"_search filter: {payload['search']}_")
        out.append("")
        links = payload.get("links") or []
        if isinstance(links, dict):
            links = links.get("links", [])
        for link in links[:200]:
            url = link if isinstance(link, str) else (link.get("url") or link.get("href") or "")
            if url:
                out.append(f"- {url}")
    elif cmd == "search":
        out.append(f"# Search: {payload['query']}")
        out.append("")
        for i, r in enumerate(payload.get("results") or [], start=1):
            if not isinstance(r, dict):
                continue
            title = r.get("title") or r.get("url") or "(untitled)"
            url = r.get("url") or ""
            out.append(f"## {i}. {title}")
            if url:
                out.append(f"<{url}>")
            snippet = r.get("description") or r.get("snippet") or ""
            if snippet:
                out.append(f"\n{snippet}")
            md = r.get("markdown")
            if md:
                # show first ~600 chars to keep output compact
                excerpt = md.strip()[:600]
                out.append(f"\n```\n{excerpt}\n```")
            out.append("")
    elif cmd == "crawl":
        out.append(f"# Crawl: {payload['url']}")
        pages = payload.get("pages") or []
        for p in pages:
            if not isinstance(p, dict):
                continue
            meta = p.get("metadata") or {}
            out.append(f"## {meta.get('title') or meta.get('url') or p.get('url')}")
            if meta.get("url") or p.get("url"):
                out.append(f"<{meta.get('url') or p.get('url')}>")
            md = p.get("markdown") or ""
            if md:
                out.append(f"\n```\n{md[:1000]}\n```\n")
    elif cmd == "extract":
        out.append(f"# Extract: {payload['url']}")
        out.append("")
        out.append("```json")
        out.append(json.dumps(payload.get("data", {}), indent=2))
        out.append("```")
    return "\n".join(out).rstrip() + "\n"


# ---------- argument parsing ----------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="firecrawl_cli.py",
        description=textwrap.dedent(__doc__),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--format",
        choices=("compact-markdown", "compact-json"),
        default="compact-markdown",
        help="output format",
    )

    sub = p.add_subparsers(dest="command", required=True)

    shared_formats = argparse.ArgumentParser(add_help=False)
    shared_formats.add_argument(
        "--format-set",
        nargs="+",
        choices=["markdown", "html", "links", "screenshot", "rawHtml"],
        help="response formats Firecrawl should return (default: markdown)",
    )

    sp_scrape = sub.add_parser("scrape", help="fetch one URL", parents=[shared_formats])
    sp_scrape.add_argument("--url", required=True)
    sp_scrape.add_argument("--full-page", action="store_true", help="include navigation/boilerplate")
    sp_scrape.add_argument("--wait-ms", type=int, default=0, help="wait ms before snapshot (JS pages)")

    sp_map = sub.add_parser("map", help="list URLs in a site")
    sp_map.add_argument("--url", required=True)
    sp_map.add_argument("--search", help="filter URLs by substring/keyword")
    sp_map.add_argument("--limit", type=int, default=200)

    sp_search = sub.add_parser("search", help="web search via Firecrawl", parents=[shared_formats])
    sp_search.add_argument("--query", required=True)
    sp_search.add_argument("--limit", type=int, default=5)
    sp_search.add_argument(
        "--scrape", action="store_true", help="also scrape result pages to markdown"
    )

    sp_crawl = sub.add_parser("crawl", help="multi-page crawl (rate-limited)", parents=[shared_formats])
    sp_crawl.add_argument("--url", required=True)
    sp_crawl.add_argument("--limit", type=int, default=20, help="max pages")
    sp_crawl.add_argument("--depth", type=int, default=2, help="max link depth")

    sp_extract = sub.add_parser("extract", help="schema-driven structured extraction")
    sp_extract.add_argument("--url", required=True)
    sp_extract.add_argument("--schema-file")
    sp_extract.add_argument("--schema-json")
    sp_extract.add_argument("--prompt", help="natural-language extraction hint")

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    fc = make_client()
    handlers = {
        "scrape": cmd_scrape,
        "map": cmd_map,
        "search": cmd_search,
        "crawl": cmd_crawl,
        "extract": cmd_extract,
    }
    payload = handlers[args.command](args, fc)
    if args.format == "compact-json":
        print(json.dumps(payload, indent=2, default=str))
    else:
        print(format_compact_markdown(args.command, payload))


if __name__ == "__main__":
    main()
