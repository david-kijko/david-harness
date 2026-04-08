from __future__ import annotations

import json
from typing import Any


def build_payload(
    *,
    route: str,
    original_query: str,
    rewritten_query: str,
    direct_answer: str | dict[str, Any] | list[Any],
    sources: list[dict[str, Any]],
    caveat: str,
    next_step: str,
    plan: dict[str, Any],
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "route": route,
        "original_query": original_query,
        "rewritten_query": rewritten_query,
        "direct_answer": direct_answer,
        "sources": [
            {
                "title": source.get("title"),
                "url": source.get("url"),
                "note": source.get("note"),
                "published_date": source.get("published_date"),
                "official": bool(source.get("official")),
            }
            for source in sources
        ],
        "caveat": caveat,
        "next_step": next_step,
        "plan": plan,
    }
    if meta:
        payload["meta"] = meta
    return payload


def _json_block(value: Any) -> str:
    return "```json\n" + json.dumps(value, indent=2, ensure_ascii=True) + "\n```"


def format_compact_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    answer = payload.get("direct_answer")
    if isinstance(answer, (dict, list)):
        lines.append(_json_block(answer))
    else:
        lines.append(str(answer).strip())

    sources = payload.get("sources", [])
    if sources:
        lines.append("")
        lines.append("Sources")
        for source in sources[:6]:
            title = source.get("title") or source.get("url") or "Untitled source"
            note = source.get("note")
            date = source.get("published_date")
            suffix = []
            if date:
                suffix.append(date)
            if source.get("official"):
                suffix.append("official")
            details = []
            if note:
                details.append(note)
            if suffix:
                details.append(", ".join(suffix))
            tail = f" - {' | '.join(details)}" if details else ""
            lines.append(f"- {title}{tail}")
            if source.get("url"):
                lines.append(f"  {source['url']}")

    lines.append("")
    lines.append(f"Caveat: {payload.get('caveat')}")
    lines.append(f"Next: {payload.get('next_step')}")
    return "\n".join(lines).strip()


def format_compact_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=True, separators=(",", ":"), default=str)


def format_output(payload: dict[str, Any], fmt: str) -> str:
    if fmt == "compact-json":
        return format_compact_json(payload)
    return format_compact_markdown(payload)
