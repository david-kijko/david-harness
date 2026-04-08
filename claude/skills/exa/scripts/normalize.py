from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING_PARAMS = {
    "fbclid",
    "gclid",
    "igshid",
    "mc_cid",
    "mc_eid",
    "mkt_tok",
    "ref",
    "ref_src",
    "s",
    "si",
    "source",
    "spm",
    "sr_share",
    "trk",
    "tracking_id",
    "utm_campaign",
    "utm_content",
    "utm_id",
    "utm_medium",
    "utm_name",
    "utm_source",
    "utm_term",
    "ved",
}

OFFICIAL_SUBDOMAIN_HINTS = (
    "api.",
    "developer.",
    "developers.",
    "docs.",
    "help.",
    "platform.",
    "reference.",
    "support.",
)

COMMUNITY_HINTS = (
    "community.",
    "discourse.",
    "forum.",
    "forums.",
    "reddit.com",
    "stackoverflow.com",
)

LOW_SIGNAL_DOMAINS = {
    "facebook.com",
    "instagram.com",
    "pinterest.com",
    "tiktok.com",
}

COMMON_DOMAIN_TOKENS = {
    "api",
    "app",
    "blog",
    "com",
    "co",
    "dev",
    "docs",
    "developer",
    "developers",
    "help",
    "io",
    "net",
    "org",
    "platform",
    "reference",
    "support",
    "www",
}

URL_RE = re.compile(r"https?://[^\s<>\]\[\"')]+", re.IGNORECASE)
DOMAIN_RE = re.compile(
    r"(?<!@)\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+(?:[a-z]{2,})(?:/[^\s<>\]\[\"')]+)?",
    re.IGNORECASE,
)


def squash_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def shorten(text: str | None, limit: int = 220) -> str:
    if not text:
        return ""
    compact = squash_whitespace(text)
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def ensure_url(value: str) -> str:
    cleaned = value.strip().strip("<>[](){}.,;")
    if re.match(r"^[a-z][a-z0-9+.-]*://", cleaned, re.IGNORECASE):
        return cleaned
    return f"https://{cleaned}"


def domain_from_url(url: str) -> str:
    try:
        parsed = urlsplit(ensure_url(url))
    except ValueError:
        return ""
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def normalize_url(url: str) -> str:
    parsed = urlsplit(ensure_url(url))
    scheme = parsed.scheme.lower() or "https"
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    if ":" in host:
        if host.endswith(":80") and scheme == "http":
            host = host[:-3]
        if host.endswith(":443") and scheme == "https":
            host = host[:-4]
    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/")
    query_pairs = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        lowered = key.lower()
        if lowered in TRACKING_PARAMS or lowered.startswith("utm_"):
            continue
        query_pairs.append((key, value))
    query = urlencode(sorted(query_pairs))
    return urlunsplit((scheme, host, path, query, ""))


def extract_urls(text: str) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()

    for match in URL_RE.findall(text):
        normalized = normalize_url(match)
        if normalized not in seen:
            ordered.append(normalized)
            seen.add(normalized)

    scrubbed = URL_RE.sub(" ", text)
    for match in DOMAIN_RE.findall(scrubbed):
        if "/" not in match and "." not in match:
            continue
        normalized = normalize_url(match)
        if normalized not in seen:
            ordered.append(normalized)
            seen.add(normalized)

    return ordered


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def parse_published_date(value: str | None) -> datetime | None:
    if not value:
        return None
    candidate = value.strip()
    if not candidate:
        return None
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
            try:
                parsed = datetime.strptime(candidate, fmt)
                break
            except ValueError:
                parsed = None
        if parsed is None:
            return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def recency_bonus(published_date: str | None, fresh: bool) -> float:
    if not fresh:
        return 0.0
    parsed = parse_published_date(published_date)
    if parsed is None:
        return -0.5
    age_days = (datetime.now(timezone.utc) - parsed).days
    if age_days <= 7:
        return 3.0
    if age_days <= 30:
        return 2.0
    if age_days <= 180:
        return 1.0
    if age_days <= 365:
        return 0.25
    return -0.75


def query_overlap_bonus(query: str, *parts: str | None) -> float:
    query_tokens = tokenize(query)
    if not query_tokens:
        return 0.0
    source_tokens = set()
    for part in parts:
        if part:
            source_tokens.update(tokenize(part))
    overlap = len(query_tokens & source_tokens)
    return min(overlap * 0.25, 2.0)


def looks_official_source(domain: str, query: str) -> bool:
    lowered = domain.lower()
    query_tokens = tokenize(query)
    domain_tokens = tokenize(lowered) - COMMON_DOMAIN_TOKENS
    brand_overlap = bool(domain_tokens & query_tokens)
    if any(lowered.startswith(prefix) for prefix in OFFICIAL_SUBDOMAIN_HINTS):
        return brand_overlap or bool(query_tokens & tokenize(lowered.replace(".", " ")))
    if any(hint in lowered for hint in COMMUNITY_HINTS):
        return False
    if brand_overlap and lowered.count(".") <= 2:
        return True
    if brand_overlap and any(token in lowered for token in OFFICIAL_SUBDOMAIN_HINTS):
        return True
    return False


def first_non_empty(*values: str | None) -> str | None:
    for value in values:
        if value:
            compact = squash_whitespace(value)
            if compact:
                return compact
    return None


def source_from_result(result: Any, query: str, note_prefix: str | None = None) -> dict[str, Any]:
    url = getattr(result, "url", None) or ""
    title = getattr(result, "title", None)
    highlights = list(getattr(result, "highlights", None) or [])
    summary = getattr(result, "summary", None)
    text = getattr(result, "text", None)
    score = getattr(result, "score", None)
    published_date = getattr(result, "published_date", None)
    note = first_non_empty(*(highlights or []), summary, text, title, url) or ""
    if note_prefix:
        note = f"{note_prefix}: {note}"
    domain = domain_from_url(url)
    return {
        "url": url,
        "normalized_url": normalize_url(url) if url else "",
        "title": title or domain or url,
        "domain": domain,
        "published_date": published_date,
        "score": score,
        "official": looks_official_source(domain, query),
        "note": shorten(note),
        "highlights": [shorten(item) for item in highlights if item],
    }


def source_from_citation(url: str, title: str | None, query: str, note: str | None = None) -> dict[str, Any]:
    normalized = normalize_url(url)
    domain = domain_from_url(url)
    return {
        "url": url,
        "normalized_url": normalized,
        "title": title or domain or url,
        "domain": domain,
        "published_date": None,
        "score": None,
        "official": looks_official_source(domain, query),
        "note": shorten(note or title or url),
        "highlights": [],
    }


def merge_source(existing: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    merged = dict(existing)
    if (candidate.get("score") or -1) > (existing.get("score") or -1):
        merged["score"] = candidate.get("score")
    if not merged.get("title") and candidate.get("title"):
        merged["title"] = candidate["title"]
    if not merged.get("published_date") and candidate.get("published_date"):
        merged["published_date"] = candidate["published_date"]
    if candidate.get("official"):
        merged["official"] = True
    notes = [existing.get("note"), candidate.get("note")]
    merged["note"] = next((note for note in notes if note), existing.get("note"))
    highlights = []
    for source in (existing, candidate):
        for item in source.get("highlights", []):
            if item and item not in highlights:
                highlights.append(item)
    merged["highlights"] = highlights[:4]
    return merged


def dedupe_sources(sources: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[str, dict[str, Any]] = {}
    ordered: list[str] = []
    for source in sources:
        key = source.get("normalized_url") or source.get("url")
        if not key:
            continue
        if key not in deduped:
            deduped[key] = dict(source)
            ordered.append(key)
        else:
            deduped[key] = merge_source(deduped[key], source)
    return [deduped[key] for key in ordered]


def rank_sources(
    sources: Iterable[dict[str, Any]],
    query: str,
    *,
    official_bias: bool,
    fresh: bool,
    explicit_domains: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    domains = {item.lower() for item in explicit_domains or [] if item}

    def rank_key(source: dict[str, Any]) -> tuple[float, str]:
        score = float(source.get("score") or 0.0) * 6.0
        if official_bias and source.get("official"):
            score += 4.0
        if domains and any(source.get("domain", "").endswith(domain) for domain in domains):
            score += 5.0
        score += recency_bonus(source.get("published_date"), fresh)
        score += query_overlap_bonus(query, source.get("title"), source.get("note"))
        if source.get("domain") in LOW_SIGNAL_DOMAINS:
            score -= 1.5
        return (score, source.get("normalized_url") or source.get("url") or "")

    return sorted(dedupe_sources(sources), key=rank_key, reverse=True)
