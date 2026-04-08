#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from formatting import build_payload, format_output
from normalize import domain_from_url, extract_urls, rank_sources, source_from_citation, source_from_result
from planning import SearchPlan, build_deep_system_prompt, build_plan, build_research_instructions, deep_output_schema


def restart_with_uv() -> None:
    if os.environ.get("CODEX_EXA_UV_FALLBACK_ACTIVE") == "1":
        return
    uv_binary = shutil.which("uv")
    if not uv_binary:
        return
    env = os.environ.copy()
    env["CODEX_EXA_UV_FALLBACK_ACTIVE"] = "1"
    os.execvpe(
        uv_binary,
        [
            uv_binary,
            "run",
            "--with",
            "exa-py",
            "python3",
            str(Path(__file__).resolve()),
            *sys.argv[1:],
        ],
        env,
    )


try:
    from exa_py import Exa
except ImportError as exc:  # pragma: no cover
    restart_with_uv()
    print(
        "exa_cli.py requires `exa-py`. Re-run via "
        "`uv run --with exa-py python3 ~/.codex/skills/exa/scripts/exa_cli.py ...`.",
        file=sys.stderr,
    )
    raise SystemExit(5) from exc


class CliError(RuntimeError):
    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(message)
        self.exit_code = exit_code


ENV_ASSIGNMENT_RE = re.compile(r"^\s*(?:export\s+)?(?P<name>[A-Za-z_][A-Za-z0-9_]*)=(?P<value>.*)\s*$")


def candidate_env_files() -> list[Path]:
    home = Path.home()
    xdg_config_home = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config")).expanduser()
    return [
        xdg_config_home / "exa" / "env.sh",
        home / ".config" / "exa" / "env.sh",
        xdg_config_home / "codex" / "env.sh",
        home / ".config" / "codex" / "env.sh",
    ]


def read_env_value(path: Path, variable_name: str) -> str:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return ""

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = ENV_ASSIGNMENT_RE.match(line)
        if not match or match.group("name") != variable_name:
            continue
        value = match.group("value").strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            return value[1:-1]
        return value
    return ""


def load_api_key() -> str:
    api_key = os.environ.get("EXA_API_KEY", "").strip()
    if api_key:
        return api_key
    for path in candidate_env_files():
        api_key = read_env_value(path, "EXA_API_KEY").strip()
        if api_key:
            os.environ["EXA_API_KEY"] = api_key
            return api_key
    raise CliError(
        "Missing EXA_API_KEY. Export it in your shell or save `export EXA_API_KEY=...` "
        "in ~/.config/exa/env.sh before running the Exa skill.",
        exit_code=2,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Codex-native Exa research CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--query", help="Research task or rewritten search query")
    shared.add_argument("--format", choices=("compact-markdown", "compact-json"), default="compact-markdown")
    shared.add_argument("--limit", type=int, default=5, help="Maximum number of sources to surface")
    shared.add_argument("--category", choices=("company", "people", "news", "research paper", "financial report"))
    shared.add_argument("--fresh", action="store_true", help="Force fresh retrieval")
    shared.add_argument("--text", action="store_true", help="Prefer full text over highlights")
    shared.add_argument("--schema-file", help="Path to a JSON schema file")
    shared.add_argument("--schema-json", help="Inline JSON schema string")
    shared.add_argument("--timeout-ms", type=int, default=300000, help="Timeout for research polling")
    shared.add_argument("--user-location", help="Two-letter ISO country code, e.g. US")

    url_shared = argparse.ArgumentParser(add_help=False)
    url_shared.add_argument("--url", action="append", default=[], help="Explicit URL or domain seed")

    subparsers.add_parser("run", parents=[shared])
    subparsers.add_parser("search", parents=[shared])
    subparsers.add_parser("contents", parents=[shared, url_shared])
    subparsers.add_parser("similar", parents=[shared, url_shared]).add_argument(
        "--exclude-source-domain",
        action="store_true",
        default=True,
        help="Exclude the seed domain from similar results",
    )
    subparsers.add_parser("answer", parents=[shared])
    subparsers.add_parser("deep-search", parents=[shared])
    subparsers.add_parser("research", parents=[shared])
    return parser


def parse_schema(args: argparse.Namespace) -> dict[str, Any] | None:
    if args.schema_json and args.schema_file:
        raise CliError("Pass either --schema-json or --schema-file, not both.", exit_code=3)
    if args.schema_json:
        try:
            return json.loads(args.schema_json)
        except json.JSONDecodeError as exc:
            raise CliError(f"Invalid --schema-json: {exc}", exit_code=3) from exc
    if args.schema_file:
        try:
            with open(args.schema_file, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except OSError as exc:
            raise CliError(f"Could not read schema file: {exc}", exit_code=3) from exc
        except json.JSONDecodeError as exc:
            raise CliError(f"Schema file is not valid JSON: {exc}", exit_code=3) from exc
    return None


def contents_options(plan: SearchPlan) -> dict[str, Any]:
    if plan.needs_text:
        options: dict[str, Any] = {
            "text": {
                "max_characters": 12000,
                "verbosity": "standard",
            }
        }
    else:
        options = {
            "highlights": {
                "query": plan.rewritten_query,
                "max_characters": 4000,
            }
        }
    if plan.fresh:
        options["max_age_hours"] = 0
        options["livecrawl"] = "always"
        options["livecrawl_timeout"] = 10000
    return options


def explicit_domains(plan: SearchPlan) -> list[str]:
    return [domain_from_url(url) for url in plan.seed_urls if url]


def plan_metadata(plan: SearchPlan) -> dict[str, Any]:
    return {
        "category": plan.category,
        "breadth": plan.breadth,
        "depth": plan.depth,
        "fresh": plan.fresh,
        "needs_text": plan.needs_text,
        "official_bias": plan.official_bias,
        "local_only": plan.local_only,
        "reason": plan.reason,
    }


def default_caveat(route: str, plan: SearchPlan, sources: list[dict[str, Any]]) -> str:
    if not sources:
        return "No usable sources came back, so this result should be treated as incomplete."
    if plan.fresh and not any(source.get("official") for source in sources[:3]):
        return "This is time-sensitive and the top hits are not clearly official, so double-check the freshest primary source."
    if route in {"search", "contents", "similar"}:
        return "This summary is based on ranked search evidence and extracted snippets rather than a full manual read of every source."
    return "Source quality looks reasonable, but you should still verify any consequential claim against the cited pages."


def default_next_step(route: str) -> str:
    if route == "contents":
        return "Open the top URL or rerun with `--text` if you need more contiguous page content."
    if route == "similar":
        return "Rerun with a narrower seed URL or category if you want a tighter competitor set."
    if route == "answer":
        return "Open the top citation or rerun with `contents` if you need the underlying page text."
    if route == "deep-search":
        return "Promote this to `research` if you want a report-grade pass with longer-running synthesis."
    if route == "research":
        return "Add a JSON schema on the next pass if you want the report in a more structured shape."
    return "Promote this to `deep-search` or `research` if you want a stronger synthesis across the sources."


def direct_answer_from_sources(route: str, plan: SearchPlan, sources: list[dict[str, Any]]) -> str:
    if not sources:
        return f"No strong web results were found for '{plan.rewritten_query}'."
    if route == "similar":
        titles = ", ".join(source.get("title") or source.get("url") for source in sources[:3])
        return f"Closest similar matches: {titles}."
    lead = sources[0]
    lead_note = lead.get("note") or lead.get("title") or lead.get("url")
    if route == "contents":
        return str(lead_note)
    if plan.category == "research paper":
        titles = ", ".join(source.get("title") or source.get("url") for source in sources[:3])
        return f"Top paper leads: {titles}."
    if plan.category == "company":
        titles = ", ".join(source.get("title") or source.get("url") for source in sources[:3])
        return f"Top company leads: {titles}."
    return f"Top sources point to: {lead_note}"


def run_parallel_searches(
    api_key: str,
    plan: SearchPlan,
    *,
    limit: int,
    user_location: str | None,
) -> list[dict[str, Any]]:
    search_kwargs = {
        "type": "auto",
        "num_results": max(limit, 5),
        "contents": contents_options(plan),
        "category": plan.category,
        "user_location": user_location,
    }

    def run_lane(lane_query: str, purpose: str) -> list[dict[str, Any]]:
        client = Exa(api_key=api_key)
        response = client.search(lane_query, **search_kwargs)
        return [source_from_result(result, plan.rewritten_query, note_prefix=purpose) for result in response.results]

    collected: list[dict[str, Any]] = []
    max_workers = min(4, max(1, len(plan.query_lanes)))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(run_lane, lane.query, lane.purpose): lane
            for lane in plan.query_lanes
        }
        for future in as_completed(futures):
            lane = futures[future]
            try:
                collected.extend(future.result())
            except Exception as exc:  # pragma: no cover
                raise CliError(f"Search lane failed for '{lane.query}': {exc}", exit_code=4) from exc
    return rank_sources(
        collected,
        plan.rewritten_query,
        official_bias=plan.official_bias,
        fresh=plan.fresh,
        explicit_domains=explicit_domains(plan),
    )[:limit]


def handle_search(api_key: str, args: argparse.Namespace, plan: SearchPlan) -> dict[str, Any]:
    sources = run_parallel_searches(
        api_key,
        plan,
        limit=args.limit,
        user_location=args.user_location,
    )
    return build_payload(
        route="search",
        original_query=plan.original_query,
        rewritten_query=plan.rewritten_query,
        direct_answer=direct_answer_from_sources("search", plan, sources),
        sources=sources,
        caveat=default_caveat("search", plan, sources),
        next_step=default_next_step("search"),
        plan=plan_metadata(plan),
        meta={"query_lanes": [lane.query for lane in plan.query_lanes]},
    )


def collect_urls(args: argparse.Namespace, plan: SearchPlan) -> list[str]:
    urls = [item for item in args.url if item] if hasattr(args, "url") else []
    urls.extend(plan.seed_urls)
    normalized = []
    seen = set()
    for url in urls:
        for candidate in extract_urls(url) or [url]:
            if candidate not in seen:
                normalized.append(candidate)
                seen.add(candidate)
    if normalized:
        return normalized
    raise CliError("No URL was provided or detected in the query.", exit_code=3)


def handle_contents(api_key: str, args: argparse.Namespace, plan: SearchPlan) -> dict[str, Any]:
    urls = collect_urls(args, plan)
    client = Exa(api_key=api_key)
    try:
        response = client.get_contents(
            urls,
            **contents_options(plan),
            filter_empty_results=True,
        )
    except Exception as exc:  # pragma: no cover
        raise CliError(f"Contents request failed: {exc}", exit_code=4) from exc
    sources = rank_sources(
        [source_from_result(result, plan.rewritten_query) for result in response.results],
        plan.rewritten_query,
        official_bias=plan.official_bias,
        fresh=plan.fresh,
        explicit_domains=explicit_domains(plan),
    )[: args.limit]
    return build_payload(
        route="contents",
        original_query=plan.original_query,
        rewritten_query=plan.rewritten_query,
        direct_answer=direct_answer_from_sources("contents", plan, sources),
        sources=sources,
        caveat=default_caveat("contents", plan, sources),
        next_step=default_next_step("contents"),
        plan=plan_metadata(plan),
        meta={"urls": urls},
    )


def handle_similar(api_key: str, args: argparse.Namespace, plan: SearchPlan) -> dict[str, Any]:
    urls = collect_urls(args, plan)
    client = Exa(api_key=api_key)
    try:
        response = client.find_similar(
            urls[0],
            num_results=max(args.limit, 5),
            exclude_source_domain=bool(getattr(args, "exclude_source_domain", True)),
            category=plan.category,
            contents=contents_options(plan),
        )
    except Exception as exc:  # pragma: no cover
        raise CliError(f"Similar request failed: {exc}", exit_code=4) from exc
    sources = rank_sources(
        [source_from_result(result, plan.rewritten_query) for result in response.results],
        plan.rewritten_query,
        official_bias=plan.official_bias,
        fresh=plan.fresh,
        explicit_domains=explicit_domains(plan),
    )[: args.limit]
    return build_payload(
        route="similar",
        original_query=plan.original_query,
        rewritten_query=plan.rewritten_query,
        direct_answer=direct_answer_from_sources("similar", plan, sources),
        sources=sources,
        caveat=default_caveat("similar", plan, sources),
        next_step=default_next_step("similar"),
        plan=plan_metadata(plan),
        meta={"seed_url": urls[0]},
    )


def handle_answer(api_key: str, args: argparse.Namespace, plan: SearchPlan) -> dict[str, Any]:
    client = Exa(api_key=api_key)
    try:
        response = client.answer(
            plan.rewritten_query,
            text=bool(plan.needs_text),
            user_location=args.user_location,
            system_prompt="Return a cited answer that is concise, direct, and grounded in the strongest sources.",
        )
    except Exception as exc:  # pragma: no cover
        raise CliError(f"Answer request failed: {exc}", exit_code=4) from exc
    sources = rank_sources(
        [
            source_from_citation(
                citation.url,
                citation.title,
                plan.rewritten_query,
                note=citation.text or citation.title,
            )
            for citation in response.citations
        ],
        plan.rewritten_query,
        official_bias=plan.official_bias,
        fresh=plan.fresh,
        explicit_domains=explicit_domains(plan),
    )[: args.limit]
    return build_payload(
        route="answer",
        original_query=plan.original_query,
        rewritten_query=plan.rewritten_query,
        direct_answer=response.answer,
        sources=sources,
        caveat=default_caveat("answer", plan, sources),
        next_step=default_next_step("answer"),
        plan=plan_metadata(plan),
    )


def grounding_sources(output: Any, query: str) -> list[dict[str, Any]]:
    collected: list[dict[str, Any]] = []
    if not output or not getattr(output, "grounding", None):
        return collected
    for grounding in output.grounding:
        for citation in grounding.citations:
            collected.append(
                source_from_citation(
                    citation.url,
                    citation.title,
                    query,
                    note=f"grounds field `{grounding.field}`",
                )
            )
    return collected


def handle_deep_search(
    api_key: str,
    args: argparse.Namespace,
    plan: SearchPlan,
    supplied_schema: dict[str, Any] | None,
) -> dict[str, Any]:
    client = Exa(api_key=api_key)
    additional_queries = [lane.query for lane in plan.query_lanes[1:]] or None
    output_schema = supplied_schema or deep_output_schema(plan.rewritten_query)
    search_type = "deep-reasoning" if plan.depth in {"D2", "D3"} or plan.schema_mode else "deep"
    try:
        response = client.search(
            plan.rewritten_query,
            type=search_type,
            num_results=max(args.limit, 5),
            category=plan.category,
            contents=contents_options(plan),
            additional_queries=additional_queries,
            system_prompt=build_deep_system_prompt(plan),
            output_schema=output_schema,
            user_location=args.user_location,
        )
    except Exception as exc:  # pragma: no cover
        raise CliError(f"Deep search failed: {exc}", exit_code=4) from exc

    sources = grounding_sources(response.output, plan.rewritten_query)
    if not sources:
        sources = [source_from_result(result, plan.rewritten_query) for result in response.results]
    ranked = rank_sources(
        sources,
        plan.rewritten_query,
        official_bias=plan.official_bias,
        fresh=plan.fresh,
        explicit_domains=explicit_domains(plan),
    )[: args.limit]

    direct_answer: str | dict[str, Any] | list[Any]
    if response.output is not None:
        direct_answer = response.output.content
    else:
        direct_answer = direct_answer_from_sources("search", plan, ranked)

    return build_payload(
        route="deep-search",
        original_query=plan.original_query,
        rewritten_query=plan.rewritten_query,
        direct_answer=direct_answer,
        sources=ranked,
        caveat=default_caveat("deep-search", plan, ranked),
        next_step=default_next_step("deep-search"),
        plan=plan_metadata(plan),
        meta={
            "search_type": search_type,
            "additional_queries": additional_queries or [],
        },
    )


def research_event_sources(events: list[Any] | None, query: str) -> list[dict[str, Any]]:
    collected: list[dict[str, Any]] = []
    for event in events or []:
        data = getattr(event, "data", None)
        if data is None:
            continue
        if getattr(data, "type", None) == "search":
            for result in getattr(data, "results", []):
                collected.append(source_from_citation(result.url, result.url, query, note="research search result"))
        elif getattr(data, "type", None) == "crawl":
            result = getattr(data, "result", None)
            if result is not None:
                collected.append(source_from_citation(result.url, result.url, query, note="research crawl target"))
    return collected


def handle_research(
    api_key: str,
    args: argparse.Namespace,
    plan: SearchPlan,
    supplied_schema: dict[str, Any] | None,
) -> dict[str, Any]:
    client = Exa(api_key=api_key)
    model = "exa-research-pro" if plan.depth == "D4" else "exa-research"
    try:
        task = client.research.create(
            instructions=build_research_instructions(plan),
            model=model,
            output_schema=supplied_schema,
        )
        result = client.research.poll_until_finished(
            task.research_id,
            timeout_ms=args.timeout_ms,
            events=True,
        )
    except Exception as exc:  # pragma: no cover
        raise CliError(f"Research request failed: {exc}", exit_code=4) from exc

    if getattr(result, "status", None) != "completed":
        raise CliError(f"Research did not complete successfully: status={getattr(result, 'status', 'unknown')}", exit_code=4)

    direct_answer = result.output.parsed if getattr(result.output, "parsed", None) else result.output.content
    sources = rank_sources(
        research_event_sources(getattr(result, "events", None), plan.rewritten_query),
        plan.rewritten_query,
        official_bias=plan.official_bias,
        fresh=plan.fresh,
        explicit_domains=explicit_domains(plan),
    )[: args.limit]

    return build_payload(
        route="research",
        original_query=plan.original_query,
        rewritten_query=plan.rewritten_query,
        direct_answer=direct_answer,
        sources=sources,
        caveat=default_caveat("research", plan, sources),
        next_step=default_next_step("research"),
        plan=plan_metadata(plan),
        meta={"model": model, "research_id": result.research_id},
    )


def dispatch(args: argparse.Namespace, schema: dict[str, Any] | None) -> dict[str, Any]:
    query = args.query or ""
    route_override = None if args.command == "run" else args.command
    if args.command in {"contents", "similar"} and not query and not getattr(args, "url", []):
        raise CliError("Pass --query, --url, or both.", exit_code=3)
    plan = build_plan(
        query or " ".join(getattr(args, "url", [])),
        category=args.category,
        fresh=args.fresh,
        needs_text=args.text,
        schema_supplied=schema is not None,
        route_override=route_override,
    )
    if plan.local_only:
        raise CliError(
            "This looks like a local repo, filesystem, database, or JavaScript fetch task rather than external web research.",
            exit_code=3,
        )
    api_key = load_api_key()
    route = plan.route

    if route == "search":
        return handle_search(api_key, args, plan)
    if route == "contents":
        return handle_contents(api_key, args, plan)
    if route == "similar":
        return handle_similar(api_key, args, plan)
    if route == "answer":
        return handle_answer(api_key, args, plan)
    if route == "deep-search":
        return handle_deep_search(api_key, args, plan, schema)
    if route == "research":
        return handle_research(api_key, args, plan, schema)
    raise CliError(f"Unsupported route: {route}", exit_code=3)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        schema = parse_schema(args)
        payload = dispatch(args, schema)
        print(format_output(payload, args.format))
        return 0
    except CliError as exc:
        print(str(exc), file=sys.stderr)
        return exc.exit_code
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130
    except Exception as exc:  # pragma: no cover
        print(f"Unexpected Exa CLI failure: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
