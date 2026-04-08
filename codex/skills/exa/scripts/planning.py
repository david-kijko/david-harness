from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re
from typing import Any

from normalize import extract_urls, squash_whitespace

FRESHNESS_TERMS = {
    "breaking",
    "changed",
    "current",
    "latest",
    "live",
    "newest",
    "now",
    "pricing changed",
    "recent",
    "today",
    "updated",
}

SIMILAR_TERMS = {
    "alternatives",
    "companies like",
    "competitor",
    "competitors",
    "lookalikes",
    "similar page",
    "similar pages",
    "similar site",
    "similar sites",
    "sites like",
}

REPORT_TERMS = {
    "comprehensive",
    "deep research",
    "due diligence",
    "exhaustive",
    "full report",
    "landscape",
    "market map",
    "report-grade",
    "research memo",
    "vendor scan",
}

DEEP_TERMS = {
    "5 whys",
    "analyze",
    "benchmark",
    "compare",
    "comparison",
    "diagnose",
    "diagnosis",
    "evaluate",
    "explain why",
    "multi-hop",
    "root cause",
    "timeline",
    "tradeoff",
    "verify",
}

DIRECT_FACT_PREFIXES = (
    "are ",
    "can ",
    "did ",
    "does ",
    "how many ",
    "is ",
    "what ",
    "when ",
    "where ",
    "which ",
    "who ",
)

STRUCTURED_TERMS = {
    "array",
    "csv",
    "fields",
    "json",
    "output schema",
    "schema",
    "structured",
    "table",
    "yaml",
}

TEXT_TERMS = {
    "code snippet",
    "exact quote",
    "full article",
    "full page",
    "full text",
    "quote",
    "read the page",
    "verbatim",
}

DOCS_TERMS = {
    "api",
    "changelog",
    "docs",
    "documentation",
    "error",
    "library",
    "reference",
    "sdk",
    "stack trace",
    "version",
}

HIGH_STAKES_TERMS = {
    "compliance",
    "earnings",
    "financial",
    "filing",
    "legal",
    "medical",
    "pricing",
    "security",
}

CATEGORY_RULES = (
    ("financial report", ("10-k", "10q", "annual report", "earnings", "filing", "investor relations", "quarterly report", "sec")),
    ("research paper", ("academic", "arxiv", "benchmark paper", "paper", "papers", "preprint", "research paper")),
    ("people", ("author", "ceo", "cto", "expert", "founder", "person", "professor", "who is")),
    ("company", ("company", "company research", "competitor", "competitors", "market research", "startup", "vendor", "vendor research")),
    ("news", ("announcement", "breaking", "current events", "headline", "news", "press release", "today")),
)

LOCAL_ONLY_HINTS = (
    "database",
    "fetch api",
    "fetch retry",
    "filesystem",
    "find this symbol in the codebase",
    "git fetch",
    "grep",
    "implement fetch",
    "local repo",
    "postgres",
    "repo",
    "ripgrep",
    "search this directory",
    "symbol in the codebase",
)

EXTERNAL_INTENT_HINTS = (
    "cited",
    "find sources",
    "look online",
    "look up",
    "online",
    "research",
    "search online",
    "search the web",
    "verify online",
    "web",
)


@dataclass(frozen=True)
class QueryLane:
    query: str
    purpose: str


@dataclass(frozen=True)
class SearchPlan:
    route: str
    original_query: str
    rewritten_query: str
    category: str | None
    breadth: str
    depth: str
    fresh: bool
    needs_text: bool
    official_bias: bool
    direct_fact: bool
    report_grade: bool
    schema_mode: bool
    local_only: bool
    seed_urls: list[str]
    query_lanes: list[QueryLane]
    reason: str


def contains_any(haystack: str, needles: set[str] | tuple[str, ...]) -> bool:
    return any(matches_term(haystack, needle) for needle in needles)


def matches_term(haystack: str, needle: str) -> bool:
    if " " in needle or "-" in needle:
        return needle in haystack
    return re.search(rf"\b{re.escape(needle)}\b", haystack) is not None


def normalize_query(query: str) -> str:
    return squash_whitespace(query.strip())


def infer_category(query: str) -> str | None:
    lowered = query.lower()
    for category, triggers in CATEGORY_RULES:
        if contains_any(lowered, triggers):
            return category
    return None


def wants_freshness(query: str) -> bool:
    return contains_any(query.lower(), FRESHNESS_TERMS)


def wants_text(query: str) -> bool:
    return contains_any(query.lower(), TEXT_TERMS)


def wants_structured_output(query: str) -> bool:
    return contains_any(query.lower(), STRUCTURED_TERMS)


def wants_official_sources(query: str) -> bool:
    lowered = query.lower()
    return contains_any(lowered, DOCS_TERMS) or "official" in lowered


def looks_report_grade(query: str) -> bool:
    lowered = query.lower()
    return contains_any(lowered, REPORT_TERMS) or lowered.startswith("research ")


def looks_like_similar_request(query: str, seed_urls: list[str]) -> bool:
    return bool(seed_urls) and contains_any(query.lower(), SIMILAR_TERMS)


def looks_like_fact_question(query: str) -> bool:
    lowered = query.lower()
    if contains_any(lowered, SIMILAR_TERMS | REPORT_TERMS | DEEP_TERMS):
        return False
    if lowered.startswith(DIRECT_FACT_PREFIXES):
        return True
    fact_phrases = (
        "current ceo",
        "latest version",
        "release date",
        "valuation",
        "when did",
        "who founded",
    )
    return contains_any(lowered, fact_phrases)


def looks_like_local_lookup(query: str) -> bool:
    lowered = query.lower()
    if contains_any(lowered, EXTERNAL_INTENT_HINTS):
        return False
    if contains_any(lowered, LOCAL_ONLY_HINTS):
        return True
    if ("repo" in lowered or "codebase" in lowered or "directory" in lowered) and contains_any(lowered, ("find", "grep", "search")):
        return True
    if contains_any(lowered, ("database", "postgres", "mysql", "sqlite")) and "fetch" in lowered:
        return True
    if "javascript" in lowered and "fetch" in lowered:
        return True
    return False


def infer_breadth(query: str, *, direct_fact: bool, report_grade: bool) -> str:
    lowered = query.lower()
    if report_grade:
        return "B3"
    if contains_any(lowered, {"alternatives", "compare", "competitor", "landscape", "market map", "vendor"}):
        return "B2"
    if direct_fact:
        return "B0"
    if "research" in lowered or "verify" in lowered or "sources" in lowered:
        return "B1"
    return "B0"


def infer_depth(query: str, *, direct_fact: bool, report_grade: bool, fresh: bool, schema_mode: bool) -> str:
    lowered = query.lower()
    if report_grade:
        return "D4"
    if schema_mode or contains_any(lowered, DEEP_TERMS | HIGH_STAKES_TERMS):
        return "D2"
    if fresh and direct_fact:
        return "D2"
    if direct_fact:
        return "D0"
    return "D1"


def lane_budget(breadth: str) -> int:
    return {
        "B0": 1,
        "B1": 2,
        "B2": 4,
        "B3": 7,
    }[breadth]


def build_query_lanes(query: str, *, category: str | None, breadth: str, fresh: bool, official_bias: bool) -> list[QueryLane]:
    budget = lane_budget(breadth)
    current_year = str(date.today().year)
    candidates: list[QueryLane] = [QueryLane(query=query, purpose="primary")]

    if category == "company":
        candidates.extend(
            [
                QueryLane(query=f"{query} official site", purpose="primary source"),
                QueryLane(query=f"{query} pricing customers funding", purpose="commercial footprint"),
                QueryLane(query=f"{query} competitors alternatives", purpose="market context"),
                QueryLane(query=f"{query} recent news {current_year}", purpose="recent updates"),
            ]
        )
    elif category == "people":
        candidates.extend(
            [
                QueryLane(query=f"{query} official profile", purpose="primary source"),
                QueryLane(query=f"{query} biography current role", purpose="identity and role"),
                QueryLane(query=f"{query} recent interview {current_year}", purpose="recent context"),
            ]
        )
    elif category == "research paper":
        candidates.extend(
            [
                QueryLane(query=f"{query} research paper", purpose="paper discovery"),
                QueryLane(query=f"{query} arxiv", purpose="academic index"),
                QueryLane(query=f"{query} benchmark {current_year}", purpose="recent evaluation"),
                QueryLane(query=f"{query} survey paper", purpose="overview"),
            ]
        )
    elif category == "financial report":
        candidates.extend(
            [
                QueryLane(query=f"{query} investor relations", purpose="issuer source"),
                QueryLane(query=f"{query} sec filing", purpose="primary filing"),
                QueryLane(query=f"{query} earnings transcript", purpose="management commentary"),
                QueryLane(query=f"{query} annual report", purpose="formal disclosure"),
            ]
        )
    else:
        if official_bias:
            candidates.extend(
                [
                    QueryLane(query=f"{query} official documentation", purpose="official docs"),
                    QueryLane(query=f"{query} reference docs", purpose="reference docs"),
                ]
            )
        if fresh:
            candidates.extend(
                [
                    QueryLane(query=f"{query} latest", purpose="fresh coverage"),
                    QueryLane(query=f"{query} {current_year}", purpose="current-year coverage"),
                ]
            )
        if "competitor" in query.lower() or "alternatives" in query.lower():
            candidates.extend(
                [
                    QueryLane(query=f"{query} comparison", purpose="comparison"),
                    QueryLane(query=f"{query} pricing", purpose="commercial comparison"),
                    QueryLane(query=f"{query} reviews", purpose="market feedback"),
                ]
            )

    unique: list[QueryLane] = []
    seen: set[str] = set()
    for candidate in candidates:
        normalized = candidate.query.lower()
        if normalized in seen:
            continue
        unique.append(QueryLane(query=normalize_query(candidate.query), purpose=candidate.purpose))
        seen.add(normalized)
        if len(unique) >= budget:
            break
    return unique


def deep_output_schema(query: str) -> dict[str, Any]:
    lowered = query.lower()
    if wants_structured_output(query) and ("table" in lowered or "compare" in lowered):
        return {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "details": {"type": "string"},
                        },
                        "required": ["name", "details"],
                    },
                },
            },
            "required": ["summary", "items"],
        }
    if wants_structured_output(query):
        return {
            "type": "object",
            "properties": {
                "answer": {"type": "string"},
                "key_points": {"type": "array", "items": {"type": "string"}},
                "open_questions": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["answer", "key_points"],
        }
    return {
        "type": "text",
        "description": "Return a concise answer with the direct result first, then key evidence, one caveat, and a concrete next step.",
    }


def build_deep_system_prompt(plan: SearchPlan) -> str:
    instructions = [
        "Prefer official and primary sources when they exist.",
        "Return the direct answer first.",
        "Keep the final synthesis compact and evidence-led.",
    ]
    if plan.fresh:
        instructions.append("Prioritize fresh sources and resolve stale evidence in favor of newer authoritative sources.")
    if plan.category == "research paper":
        instructions.append("Prefer papers, official project pages, and benchmark writeups over generic blogs.")
    if plan.category == "financial report":
        instructions.append("Prefer issuer filings, investor relations pages, and primary financial disclosures.")
    if plan.category == "people":
        instructions.append("Prefer official bios, company pages, and direct interviews over secondary summaries.")
    return " ".join(instructions)


def build_research_instructions(plan: SearchPlan) -> str:
    requirements = [
        f"Research task: {plan.rewritten_query}",
        "Return the direct answer first, then key evidence, one caveat, and one concrete next step.",
        "Prefer official and primary sources when available.",
        "Use multiple sources and cross-check disagreements.",
    ]
    if plan.fresh:
        requirements.append("Prioritize recent sources and fresh evidence.")
    if plan.category:
        requirements.append(f"Focus the search on the `{plan.category}` category when helpful.")
    if plan.official_bias:
        requirements.append("Bias toward official documentation and first-party pages.")
    return " ".join(requirements)


def build_plan(
    query: str,
    *,
    category: str | None = None,
    fresh: bool = False,
    needs_text: bool = False,
    schema_supplied: bool = False,
    route_override: str | None = None,
) -> SearchPlan:
    rewritten_query = normalize_query(query)
    seed_urls = extract_urls(rewritten_query)
    inferred_category = category or infer_category(rewritten_query)
    inferred_fresh = fresh or wants_freshness(rewritten_query)
    inferred_text = needs_text or wants_text(rewritten_query)
    schema_mode = schema_supplied or wants_structured_output(rewritten_query)
    official_bias = wants_official_sources(rewritten_query)
    report_grade = looks_report_grade(rewritten_query)
    direct_fact = looks_like_fact_question(rewritten_query)
    local_only = looks_like_local_lookup(rewritten_query)
    breadth = infer_breadth(rewritten_query, direct_fact=direct_fact, report_grade=report_grade)
    depth = infer_depth(
        rewritten_query,
        direct_fact=direct_fact,
        report_grade=report_grade,
        fresh=inferred_fresh,
        schema_mode=schema_mode,
    )

    if route_override:
        route = route_override
        reason = f"explicit {route_override} subcommand"
    elif seed_urls and looks_like_similar_request(rewritten_query, seed_urls):
        route = "similar"
        reason = "query asks for similar pages or competitors from a known URL/domain"
    elif seed_urls:
        route = "contents"
        reason = "query includes explicit URLs"
    elif report_grade:
        route = "research"
        reason = "query looks exhaustive or report-grade"
    elif inferred_fresh and direct_fact:
        route = "deep-search"
        reason = "time-sensitive fact question requires fresh synthesized evidence"
    elif schema_mode or contains_any(rewritten_query.lower(), DEEP_TERMS):
        route = "deep-search"
        reason = "query needs structured or multi-hop synthesis"
    elif direct_fact:
        route = "answer"
        reason = "query is a direct fact question suited to cited short-form answering"
    else:
        route = "search"
        reason = "query is ordinary web research"

    lanes = build_query_lanes(
        rewritten_query,
        category=inferred_category,
        breadth=breadth,
        fresh=inferred_fresh,
        official_bias=official_bias,
    )

    return SearchPlan(
        route=route,
        original_query=query,
        rewritten_query=rewritten_query,
        category=inferred_category,
        breadth=breadth,
        depth=depth,
        fresh=inferred_fresh,
        needs_text=inferred_text,
        official_bias=official_bias,
        direct_fact=direct_fact,
        report_grade=report_grade,
        schema_mode=schema_mode,
        local_only=local_only,
        seed_urls=seed_urls,
        query_lanes=lanes,
        reason=reason,
    )
