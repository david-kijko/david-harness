#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


COMPONENT_BLUEPRINTS = [
    {
        "name": "Intent compiler",
        "what_it_does": "Rewrites an open-ended ask into an operational brief with hidden deliverables, evidence targets, and completion criteria.",
        "evidence": "The user provided examples of reframing vague work into a concrete investigative brief before execution.",
        "build_requirement": "Add a first-class latent-requirements compiler before planning begins.",
    },
    {
        "name": "Research orchestrator",
        "what_it_does": "Fans out research threads by topic, source type, or uncertainty bucket and merges them back into shared synthesis state.",
        "evidence": "The user described repeated parallel task execution across multiple research tracks.",
        "build_requirement": "Provide true fan-out and fan-in orchestration instead of strictly sequential state flow.",
    },
    {
        "name": "Plan / task ledger",
        "what_it_does": "Maintains visible checklist tasks, statuses, and next actions throughout the session.",
        "evidence": "The user described named planning objects and checklist-style execution.",
        "build_requirement": "Persist a user-visible task ledger rather than relying on transient routing state.",
    },
    {
        "name": "Source-tiered evidence layer",
        "what_it_does": "Distinguishes reconnaissance from authoritative sources and escalates toward primary documentation before final synthesis.",
        "evidence": "The user described broad research that tightened into official documentation before artifact generation.",
        "build_requirement": "Add explicit authority ranking and coverage closure logic.",
    },
    {
        "name": "Synthesis engine",
        "what_it_does": "Consolidates thread outputs into a coherent model, decides when enough evidence exists, and structures the deliverable.",
        "evidence": "The user described a transition from parallel research to a comprehensive-picture synthesis state.",
        "build_requirement": "Track synthesis completeness with richer state than simple report heuristics.",
    },
    {
        "name": "Artifact builder",
        "what_it_does": "Uses code generation to produce final deliverables with layout control and export fidelity.",
        "evidence": "The user described a document builder step creating an analysis artifact.",
        "build_requirement": "Provide a render pipeline with markdown, HTML, PDF, and DOCX backends.",
    },
    {
        "name": "Telemetry / audit layer",
        "what_it_does": "Captures process, tool usage, evidence provenance, and artifact lineage for later forensic replay.",
        "evidence": "The user described telemetry, logs, monitoring, and lineage as part of the analysis process.",
        "build_requirement": "Design requirement-linked observability separately from the rest of the orchestration loop.",
    },
]

LATENT_RULES = [
    {
        "keywords": ["research", "analyze", "analysis", "investigate", "forensic"],
        "latent_requirements": [
            "Capture an evidence-backed summary instead of only raw notes.",
            "Surface key uncertainties and what additional evidence would close them.",
        ],
        "evidence_targets": [
            "Primary documentation or authoritative product pages.",
            "Cross-checking evidence from at least one secondary source.",
        ],
        "artifact_targets": ["markdown-report"],
        "superpowers": ["exa"],
    },
    {
        "keywords": ["compare", "comparison", "competitive", "landscape", "benchmark"],
        "latent_requirements": [
            "Include a comparison matrix that highlights meaningful differentiators.",
            "Add a recommendation or decision framing, not just a feature dump.",
        ],
        "evidence_targets": [
            "Pricing, capability, and positioning evidence from official sources.",
        ],
        "artifact_targets": ["table", "markdown-report"],
        "superpowers": ["exa"],
    },
    {
        "keywords": ["build", "implement", "ship", "code", "patch", "feature"],
        "latent_requirements": [
            "Include verification steps or tests for any implementation output.",
            "Call out rollout or integration risks before considering the work complete.",
        ],
        "evidence_targets": [
            "Local code evidence, tests, and repository context.",
        ],
        "artifact_targets": ["code", "markdown-report"],
        "superpowers": ["native-codex"],
    },
    {
        "keywords": ["pdf", "docx", "document", "report", "brief"],
        "latent_requirements": [
            "Preserve layout and export fidelity for the final deliverable.",
        ],
        "evidence_targets": [
            "A build path that can render the artifact to the requested format.",
        ],
        "artifact_targets": ["markdown-report", "pdf"],
        "superpowers": ["native-codex"],
    },
    {
        "keywords": ["openai", "gpt", "chatgpt", "responses api", "assistants api"],
        "latent_requirements": [
            "Prefer official OpenAI documentation before relying on third-party summaries.",
        ],
        "evidence_targets": [
            "Official OpenAI documentation or product references.",
        ],
        "artifact_targets": ["markdown-report"],
        "superpowers": ["openai-docs"],
    },
    {
        "keywords": ["conductor", "track", "workflow", "requirements matrix"],
        "latent_requirements": [
            "Align work products with the expected workflow artifacts and state transitions.",
        ],
        "evidence_targets": [
            "Existing conductor or superconductor workflow files in the repository.",
        ],
        "artifact_targets": ["markdown-report", "json"],
        "superpowers": ["conductor", "superconductor"],
    },
]

SUPERPOWER_RULES = [
    (r"\b(latest|current|recent|news|research|sources?|pricing|vendor|market|compare|competitive)\b", "exa"),
    (r"\b(openai|gpt|chatgpt|responses api|assistants api)\b", "openai-docs"),
    (r"\b(conductor|workflow|track|requirements matrix)\b", "conductor"),
    (r"\b(superconductor|autonomous spec|run the pipeline)\b", "superconductor"),
    (r"\b(code|implement|patch|test|repo|repository|shell|script)\b", "native-codex"),
]

ARTIFACT_RULES = [
    (r"\bpdf\b", "pdf"),
    (r"\bdocx\b", "docx"),
    (r"\bhtml\b", "html"),
    (r"\bjson\b", "json"),
    (r"\bcsv\b", "csv"),
    (r"\btable|matrix|comparison\b", "table"),
    (r"\bcode|patch|script|implementation\b", "code"),
    (r"\breport|brief|memo|analysis|investigation\b", "markdown-report"),
]

PRIMARY_KEYWORDS = {
    "official",
    "api",
    "docs",
    "documentation",
    "spec",
    "specification",
    "pricing",
    "policy",
    "legal",
    "compliance",
    "telemetry",
    "otel",
    "monitoring",
}

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "i",
    "in",
    "into",
    "is",
    "it",
    "me",
    "of",
    "on",
    "or",
    "our",
    "so",
    "that",
    "the",
    "this",
    "to",
    "up",
    "use",
    "we",
    "with",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def slugify(text: str, limit: int = 48) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    return slug[:limit].strip("-") or "run"


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def write_json(path: Path, payload: Any) -> None:
    ensure_parent(path)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def write_text(path: Path, text: str) -> None:
    ensure_parent(path)
    path.write_text(text)


def unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item and item not in seen:
            ordered.append(item)
            seen.add(item)
    return ordered


def extract_query(args: argparse.Namespace) -> str:
    if getattr(args, "query", None):
        return args.query.strip()
    if getattr(args, "query_file", None):
        return Path(args.query_file).read_text().strip()
    raise SystemExit("Provide --query or --query-file.")


def extract_text_tokens(text: str) -> list[str]:
    return [token for token in re.findall(r"[A-Za-z0-9][A-Za-z0-9_-]{2,}", text.lower()) if token not in STOPWORDS]


def split_clauses(text: str) -> list[str]:
    normalized = text.replace("\n", ". ")
    raw_parts = re.split(r"\.\s+|;\s+|\?\s+|\!\s+|\s+-\s+|\s+and\s+(?=[a-z])", normalized)
    clauses = [part.strip(" .\t") for part in raw_parts if part.strip(" .\t")]
    return clauses or [text.strip()]


def infer_entities(text: str) -> list[str]:
    backticked = re.findall(r"`([^`]+)`", text)
    titled = re.findall(r"\b(?:[A-Z][a-z0-9]+(?:\s+[A-Z][a-z0-9]+)+)\b", text)
    return unique(backticked + titled)


def make_requirement_objects(prefix: str, texts: list[str]) -> list[dict[str, Any]]:
    return [{"id": f"{prefix}-{index:03d}", "text": value} for index, value in enumerate(unique(texts), start=1)]


def infer_explicit_requirements(query: str) -> list[dict[str, Any]]:
    clauses = []
    for clause in split_clauses(query):
        cleaned = clause.strip()
        if len(cleaned.split()) >= 3:
            clauses.append(cleaned[0].upper() + cleaned[1:] if cleaned else cleaned)
    if not clauses:
        clauses = [query.strip()]
    return make_requirement_objects("EXP", clauses)


def infer_latent_requirements(query: str) -> tuple[list[dict[str, Any]], list[str], list[str], list[str]]:
    lower = query.lower()
    latent_texts: list[str] = []
    evidence_targets: list[str] = []
    artifact_targets: list[str] = []
    superpowers: list[str] = []

    for rule in LATENT_RULES:
        if any(keyword in lower for keyword in rule["keywords"]):
            latent_texts.extend(rule["latent_requirements"])
            evidence_targets.extend(rule["evidence_targets"])
            artifact_targets.extend(rule["artifact_targets"])
            superpowers.extend(rule["superpowers"])

    if not re.search(r"\b(recommend|recommendation|decision)\b", lower):
        latent_texts.append("Provide a recommendation, prioritization, or next-step framing when the output could drive a decision.")
    if not re.search(r"\b(risk|gap|uncertainty)\b", lower):
        latent_texts.append("Call out the main risks, gaps, or unresolved questions explicitly.")
    if "parallel" in lower or "swarm" in lower:
        latent_texts.append("Partition the work into independent lanes that can be synthesized back into a shared state.")

    latent_requirements = make_requirement_objects("LAT", latent_texts)
    return latent_requirements, unique(evidence_targets), unique(artifact_targets), unique(superpowers)


def infer_superpowers(query: str, inferred: list[str]) -> list[str]:
    selected = list(inferred)
    lower = query.lower()
    for pattern, skill_name in SUPERPOWER_RULES:
        if re.search(pattern, lower):
            selected.append(skill_name)
    if not selected:
        selected.append("native-codex")
    return unique(selected)


def infer_artifact_targets(query: str, inferred: list[str]) -> list[str]:
    selected = list(inferred)
    lower = query.lower()
    for pattern, target in ARTIFACT_RULES:
        if re.search(pattern, lower):
            selected.append(target)
    if not selected:
        selected.append("markdown-report")
    return unique(selected)


def infer_authority_sources(query: str, evidence_targets: list[str]) -> list[str]:
    authority: list[str] = []
    combined = " ".join([query] + evidence_targets).lower()
    if any(keyword in combined for keyword in PRIMARY_KEYWORDS):
        authority.append("primary")
    if "peer" in combined or "analysis" in combined or "secondary" in combined:
        authority.append("secondary")
    authority.append("recon")
    return unique(authority)


def score_complexity(
    query: str,
    explicit: list[dict[str, Any]],
    latent: list[dict[str, Any]],
    evidence_targets: list[str],
    artifact_targets: list[str],
) -> dict[str, Any]:
    lower = query.lower()
    ambiguity_words = len(re.findall(r"\b(best|better|help|figure out|complex|think through|some|something)\b", lower))
    artifact_count = len(artifact_targets)
    domain_signals = sum(
        bool(re.search(pattern, lower))
        for pattern in [
            r"\b(code|repo|test|patch)\b",
            r"\b(research|market|sources?|compare)\b",
            r"\b(document|report|pdf|docx|brief)\b",
            r"\b(telemetry|monitoring|otel|observability)\b",
            r"\b(legal|compliance|pricing|policy)\b",
        ]
    )
    evidence_difficulty = len(evidence_targets) + len(re.findall(r"\b(latest|current|recent|official|legal|pricing)\b", lower))

    breakdown = {
        "ambiguity": min(5, 1 + ambiguity_words + max(0, len(latent) - len(explicit)) // 2),
        "breadth_of_domains": min(5, max(1, domain_signals)),
        "depth_of_expertise_required": min(5, 1 + len(re.findall(r"\b(architecture|forensic|legal|observability|compliance|synthesis)\b", lower))),
        "data_gathering_difficulty": min(5, max(1, evidence_difficulty)),
        "artifact_complexity": min(5, max(1, artifact_count + len(re.findall(r"\b(table|matrix|compare|render|export)\b", lower)))),
    }
    total = sum(breakdown.values())
    if total >= 15:
        execution_mode = "full-swarm"
    elif total >= 8:
        execution_mode = "selective-parallel"
    else:
        execution_mode = "single-agent"
    return {"breakdown": breakdown, "total": total, "execution_mode": execution_mode}


def build_completion_criteria(
    explicit: list[dict[str, Any]],
    latent: list[dict[str, Any]],
    artifact_targets: list[str],
) -> list[dict[str, Any]]:
    criteria: list[dict[str, Any]] = []
    counter = 1
    for requirement in explicit + latent:
        criteria.append(
            {
                "id": f"CR-{counter:03d}",
                "requirement_id": requirement["id"],
                "requirement": requirement["text"],
                "evidence_needed": "At least one corroborating evidence item, implementation artifact, or verified output aligned to this requirement.",
                "done_when": "The requirement is addressed in the synthesis and reflected in the final artifact.",
            }
        )
        counter += 1
    for target in artifact_targets:
        criteria.append(
            {
                "id": f"CR-{counter:03d}",
                "requirement_id": f"ART-{counter:03d}",
                "requirement": f"Produce the requested `{target}` artifact or an equivalent exported deliverable.",
                "evidence_needed": "A generated artifact path or renderable output.",
                "done_when": "The artifact exists and matches the requested format closely enough to be useful.",
            }
        )
        counter += 1
    return criteria


def build_intent_contract(query: str, context_text: str = "") -> dict[str, Any]:
    explicit = infer_explicit_requirements(query)
    latent, evidence_targets, inferred_artifacts, inferred_superpowers = infer_latent_requirements(query + "\n" + context_text)
    artifact_targets = infer_artifact_targets(query + "\n" + context_text, inferred_artifacts)
    selected_superpowers = infer_superpowers(query + "\n" + context_text, inferred_superpowers)
    completion_criteria = build_completion_criteria(explicit, latent, artifact_targets)
    complexity = score_complexity(query + "\n" + context_text, explicit, latent, evidence_targets, artifact_targets)

    contract = {
        "query": query,
        "entities": infer_entities(query),
        "explicit_requirements": explicit,
        "latent_requirements": latent,
        "evidence_targets": evidence_targets,
        "completion_criteria": completion_criteria,
        "complexity_score": complexity["total"],
        "complexity_breakdown": complexity["breakdown"],
        "execution_mode": complexity["execution_mode"],
        "selected_superpowers": selected_superpowers,
        "authority_sources_needed": infer_authority_sources(query, evidence_targets),
        "artifact_targets": artifact_targets,
        "quality_thresholds": {
            "pass_threshold": 85,
            "partial_threshold": 60,
            "max_internal_loops": 2,
            "max_exa_escalations": 2,
        },
    }
    return {
        "intent_contract": contract,
        "component_blueprints": COMPONENT_BLUEPRINTS,
        "generated_at": now_iso(),
    }


def extract_contract(data: dict[str, Any]) -> dict[str, Any]:
    return data.get("intent_contract", data)


def route_superpower(requirement_text: str, selected_superpowers: list[str]) -> str:
    lower = requirement_text.lower()
    for preferred in ["openai-docs", "exa", "superconductor", "conductor", "native-codex"]:
        if preferred in selected_superpowers:
            if preferred == "exa" and re.search(r"\b(source|research|pricing|market|compare|official)\b", lower):
                return preferred
            if preferred == "openai-docs" and re.search(r"\b(openai|gpt|chatgpt)\b", lower):
                return preferred
            if preferred == "native-codex" and re.search(r"\b(code|test|patch|script|artifact)\b", lower):
                return preferred
    return selected_superpowers[0] if selected_superpowers else "native-codex"


def authority_tier_for_requirement(text: str) -> str:
    lower = text.lower()
    if any(keyword in lower for keyword in PRIMARY_KEYWORDS):
        return "primary"
    if "analysis" in lower or "peer" in lower:
        return "secondary"
    return "recon"


def lane_name(index: int, max_lanes: int) -> str:
    lane_index = index % max_lanes
    return chr(ord("A") + lane_index)


def build_task_ledger(intent_contract: dict[str, Any], max_lanes: int) -> dict[str, Any]:
    requirements = intent_contract["explicit_requirements"] + intent_contract["latent_requirements"]
    tasks: list[dict[str, Any]] = []
    swarm_lanes: dict[str, list[str]] = defaultdict(list)

    for index, requirement in enumerate(requirements, start=1):
        lane = lane_name(index - 1, max_lanes)
        task_id = f"T-{index:03d}"
        task = {
            "id": task_id,
            "description": requirement["text"],
            "requirement_id": requirement["id"],
            "assigned_superpower": route_superpower(requirement["text"], intent_contract["selected_superpowers"]),
            "swarm_lane": lane,
            "status": "pending",
            "depends_on": [],
            "evidence_slot": f"evidence/{requirement['id']}.json",
            "authority_tier": authority_tier_for_requirement(requirement["text"]),
        }
        tasks.append(task)
        swarm_lanes[lane].append(task_id)

    synthesis_task_id = f"T-{len(tasks) + 1:03d}"
    artifact_task_id = f"T-{len(tasks) + 2:03d}"
    quality_task_id = f"T-{len(tasks) + 3:03d}"
    dependency_ids = [task["id"] for task in tasks]

    tasks.extend(
        [
            {
                "id": synthesis_task_id,
                "description": "Merge evidence across lanes into synthesis state.",
                "requirement_id": "SYNTHESIS",
                "assigned_superpower": "native-codex",
                "swarm_lane": "S",
                "status": "pending",
                "depends_on": dependency_ids,
                "evidence_slot": "artifacts/synthesis_state.json",
                "authority_tier": "secondary",
            },
            {
                "id": artifact_task_id,
                "description": "Build the final artifact in the requested format.",
                "requirement_id": "ARTIFACT",
                "assigned_superpower": "native-codex",
                "swarm_lane": "B",
                "status": "pending",
                "depends_on": [synthesis_task_id],
                "evidence_slot": "artifacts/final_artifact.md",
                "authority_tier": "secondary",
            },
            {
                "id": quality_task_id,
                "description": "Run the quality gate and decide whether remediation or escalation is required.",
                "requirement_id": "QUALITY",
                "assigned_superpower": "native-codex",
                "swarm_lane": "Q",
                "status": "pending",
                "depends_on": [artifact_task_id],
                "evidence_slot": "artifacts/quality_report.json",
                "authority_tier": "secondary",
            },
        ]
    )

    return {
        "task_ledger": tasks,
        "swarm_lanes": dict(swarm_lanes),
        "generated_at": now_iso(),
    }


def normalize_tier(value: Any) -> int:
    if isinstance(value, int):
        return min(3, max(1, value))
    mapping = {"primary": 1, "authoritative": 1, "tier1": 1, "1": 1, "secondary": 2, "tier2": 2, "2": 2, "recon": 3, "tier3": 3, "3": 3}
    return mapping.get(str(value).strip().lower(), 3)


def tier_label(value: int) -> str:
    return {1: "primary", 2: "secondary", 3: "recon"}[value]


def load_evidence_records(evidence_dir: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not evidence_dir.exists():
        return records
    for path in sorted(evidence_dir.rglob("*.json")):
        payload = load_json(path)
        if isinstance(payload, list):
            for item in payload:
                if isinstance(item, dict):
                    records.append({**item, "_path": str(path)})
        elif isinstance(payload, dict):
            records.append({**payload, "_path": str(path)})
    return records


def build_synthesis_state(
    intent_contract: dict[str, Any],
    task_ledger: list[dict[str, Any]],
    evidence_records: list[dict[str, Any]],
) -> dict[str, Any]:
    bucketed: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in evidence_records:
        requirement_id = record.get("requirement_id") or record.get("criterion_id")
        if requirement_id:
            bucketed[str(requirement_id)].append(record)

    evidence_by_requirement: dict[str, Any] = {}
    unmet_criteria: list[str] = []
    criteria = intent_contract["completion_criteria"]

    for criterion in criteria:
        requirement_id = criterion["requirement_id"]
        items = bucketed.get(requirement_id, [])
        if items:
            normalized_tiers = [normalize_tier(item.get("tier", 3)) for item in items]
            best_tier = min(normalized_tiers)
            confidence_values = [float(item.get("confidence", 0.7)) for item in items if item.get("confidence") is not None]
            evidence_by_requirement[requirement_id] = {
                "evidence": items,
                "tier": best_tier,
                "tier_label": tier_label(best_tier),
                "confidence": round(sum(confidence_values) / len(confidence_values), 3) if confidence_values else 0.7,
            }
        else:
            unmet_criteria.append(criterion["id"])

    met = len(criteria) - len(unmet_criteria)
    coverage_score = round((met / len(criteria)) if criteria else 0.0, 3)

    task_status = Counter(task["status"] for task in task_ledger)

    return {
        "synthesis_state": {
            "evidence_by_requirement": evidence_by_requirement,
            "unmet_criteria": unmet_criteria,
            "coverage_score": coverage_score,
            "task_status_summary": dict(task_status),
        },
        "generated_at": now_iso(),
    }


def keyword_overlap(requirement_text: str, artifact_text: str) -> float:
    req_tokens = set(extract_text_tokens(requirement_text))
    artifact_tokens = set(extract_text_tokens(artifact_text))
    if not req_tokens:
        return 0.0
    return len(req_tokens & artifact_tokens) / len(req_tokens)


def build_artifact_payload(intent_contract: dict[str, Any], synthesis_state: dict[str, Any], output_format: str) -> dict[str, Any]:
    sections = [
        "Overview",
        "Explicit Requirements",
        "Latent Requirements",
        "Evidence Targets",
        "Execution Mode",
        "Evidence Coverage",
        "Risks And Gaps",
        "Next Actions",
    ]
    evidence_summary = synthesis_state.get("evidence_by_requirement", {})
    unmet = synthesis_state.get("unmet_criteria", [])

    markdown = "\n".join(
        [
            "# Uncommon Sense Output",
            "",
            "## Overview",
            intent_contract["query"],
            "",
            "## Explicit Requirements",
            *[f"- {item['id']}: {item['text']}" for item in intent_contract["explicit_requirements"]],
            "",
            "## Latent Requirements",
            *[f"- {item['id']}: {item['text']}" for item in intent_contract["latent_requirements"]],
            "",
            "## Evidence Targets",
            *[f"- {item}" for item in intent_contract["evidence_targets"]],
            "",
            "## Execution Mode",
            f"- Complexity score: {intent_contract['complexity_score']}",
            f"- Mode: {intent_contract['execution_mode']}",
            f"- Superpowers: {', '.join(intent_contract['selected_superpowers'])}",
            "",
            "## Evidence Coverage",
            *(f"- {requirement_id}: tier {entry['tier']} ({entry['tier_label']}), confidence {entry['confidence']}" for requirement_id, entry in evidence_summary.items()),
            "",
            "## Risks And Gaps",
            *(["- No unmet criteria recorded."] if not unmet else [f"- {criterion_id}" for criterion_id in unmet]),
            "",
            "## Next Actions",
            "- Run targeted remediation for unmet criteria if quality remains below threshold.",
            "- Escalate to exa for deeper research if evidence quality is too weak.",
            "",
        ]
    )

    payload: dict[str, Any]
    if output_format == "json":
        payload = {
            "query": intent_contract["query"],
            "explicit_requirements": intent_contract["explicit_requirements"],
            "latent_requirements": intent_contract["latent_requirements"],
            "evidence_targets": intent_contract["evidence_targets"],
            "execution_mode": intent_contract["execution_mode"],
            "evidence_summary": evidence_summary,
            "unmet_criteria": unmet,
        }
        final_artifact: Any = payload
    else:
        final_artifact = markdown

    return {
        "final_artifact": final_artifact,
        "artifact_metadata": {
            "format": output_format,
            "sections": sections,
            "citation_map": {rid: entry["tier_label"] for rid, entry in evidence_summary.items()},
            "render_targets_available": ["md", "html", "pdf", "docx", "json"],
        },
        "generated_at": now_iso(),
    }


def read_artifact_text(path: Path | None) -> str:
    if not path or not path.exists():
        return ""
    if path.suffix.lower() == ".json":
        try:
            return json.dumps(load_json(path))
        except json.JSONDecodeError:
            return path.read_text()
    return path.read_text()


def run_quality_gate(intent_contract: dict[str, Any], synthesis_state: dict[str, Any], artifact_text: str) -> dict[str, Any]:
    criteria = intent_contract["completion_criteria"]
    evidence_by_requirement = synthesis_state.get("evidence_by_requirement", {})
    scores: list[dict[str, Any]] = []

    for criterion in criteria:
        requirement_id = criterion["requirement_id"]
        evidence = evidence_by_requirement.get(requirement_id)
        overlap = keyword_overlap(criterion["requirement"], artifact_text)
        score = 0
        rationale = "Requirement not yet reflected in evidence or artifact."
        if evidence or overlap >= 0.15:
            score = 1
            rationale = "Requirement appears partially addressed."
        if evidence and overlap >= 0.15:
            score = 2
            rationale = "Requirement is covered by evidence and reflected in the artifact."
        if evidence and evidence["tier"] <= 2 and evidence["confidence"] >= 0.85 and overlap >= 0.2:
            score = 3
            rationale = "Requirement is exceeded with strong evidence quality and clear artifact coverage."
        elif evidence and evidence["tier"] <= 2 and evidence["confidence"] >= 0.75:
            score = max(score, 2)
            rationale = "Requirement is fully met with acceptable evidence quality."
        scores.append(
            {
                "criterion_id": criterion["id"],
                "requirement_id": requirement_id,
                "score": score,
                "rationale": rationale,
            }
        )

    total_possible = len(criteria) * 3 if criteria else 1
    total_score = sum(item["score"] for item in scores)
    intent_fidelity_score = round((total_score / total_possible) * 100, 2)
    thresholds = intent_contract["quality_thresholds"]

    if intent_fidelity_score >= thresholds["pass_threshold"]:
        decision = "pass"
    elif intent_fidelity_score >= thresholds["partial_threshold"]:
        decision = "remediate"
    else:
        decision = "escalate_to_exa"

    unmet = [item["criterion_id"] for item in scores if item["score"] < 2]

    return {
        "quality_report": {
            "intent_fidelity_score": intent_fidelity_score,
            "decision": decision,
            "thresholds": thresholds,
            "criterion_scores": scores,
            "unmet_criteria": unmet,
            "summary": f"Intent fidelity {intent_fidelity_score}% -> {decision}.",
        },
        "generated_at": now_iso(),
    }


def build_telemetry_snapshot(
    intent_contract: dict[str, Any],
    task_ledger: list[dict[str, Any]],
    synthesis_state: dict[str, Any],
    artifact_metadata: dict[str, Any],
    quality_report: dict[str, Any],
    run_id: str | None = None,
) -> dict[str, Any]:
    provenance_chain = []
    for requirement_id, entry in synthesis_state.get("evidence_by_requirement", {}).items():
        for evidence in entry.get("evidence", []):
            provenance_chain.append(
                {
                    "requirement_id": requirement_id,
                    "source": evidence.get("source") or evidence.get("url") or evidence.get("title") or evidence.get("_path"),
                    "tier": entry["tier_label"],
                    "confidence": evidence.get("confidence", entry.get("confidence")),
                }
            )

    return {
        "audit_log": {
            "session_id": run_id or slugify(intent_contract["query"]),
            "generated_at": now_iso(),
            "phases_completed": [
                "intent_compile",
                "task_ledger",
                "synthesis",
                "artifact_build",
                "quality_gate",
            ],
            "superpowers_invoked": intent_contract["selected_superpowers"],
            "task_status_counts": dict(Counter(task["status"] for task in task_ledger)),
            "provenance_chain": provenance_chain,
            "quality_gate_results": quality_report,
            "artifact_metadata": artifact_metadata,
        }
    }


def build_agent_team_brief(intent_contract: dict[str, Any], task_ledger: list[dict[str, Any]]) -> dict[str, Any]:
    lane_tasks: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for task in task_ledger:
        lane = task.get("swarm_lane")
        if lane and lane not in {"S", "B", "Q"}:
            lane_tasks[lane].append(task)

    sorted_lanes = sorted(lane_tasks.items(), key=lambda item: item[0])
    roles: list[dict[str, Any]] = []
    for lane, tasks in sorted_lanes:
        task_text = "; ".join(task["description"] for task in tasks[:3])
        role_name = f"lane-{lane.lower()}-lead"
        roles.append(
            {
                "lane": lane,
                "role": role_name,
                "focus": task_text or "Handle the assigned lane work and report findings back to the lead.",
                "task_ids": [task["id"] for task in tasks],
            }
        )

    if not roles:
        roles.append(
            {
                "lane": "A",
                "role": "research-lead",
                "focus": "Handle the core work and report findings back to the lead.",
                "task_ids": [],
            }
        )

    role_lines = [
        f"- {role['role']}: lane {role['lane']} owning tasks {', '.join(role['task_ids']) or 'none yet'}; focus: {role['focus']}"
        for role in roles
    ]

    approval_clause = (
        "Require plan approval for any teammate that will make code changes or broad file edits."
    )

    lead_prompt = "\n".join(
        [
            "Create a delegated team for this request.",
            f"User request: {intent_contract['query']}",
            f"Execution mode: {intent_contract['execution_mode']}",
            "Keep the lead session focused on orchestration, synthesis, and quality gating.",
            "Use teammates to fan out the parallel lanes below so each lane stays in its own context window.",
            *role_lines,
            "Seed the shared task list from the lane assignments and let teammates self-claim only unblocked work.",
            approval_clause,
            "After teammate work completes, synthesize the results in the lead session, run the quality gate, and decide whether remediation or exa escalation is needed.",
        ]
    )

    return {
        "agent_team_brief": {
            "recommended_teammate_count": len(roles),
            "roles": roles,
            "lead_prompt": lead_prompt,
            "notes": [
                "Use delegated lanes only when parallel work is explicitly authorized.",
                "Official Claude docs note that agent teams increase total token usage even while reducing pressure on the lead context window.",
            ],
        },
        "generated_at": now_iso(),
    }


def init_run(workspace: Path, query: str) -> dict[str, Any]:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{timestamp}-{slugify(query)}"
    run_dir = workspace / run_id
    (run_dir / "evidence").mkdir(parents=True, exist_ok=True)
    (run_dir / "artifacts").mkdir(parents=True, exist_ok=True)
    write_text(run_dir / "query.txt", query + "\n")
    write_json(run_dir / "component_blueprints.json", {"components": COMPONENT_BLUEPRINTS, "generated_at": now_iso()})
    return {"run_id": run_id, "run_dir": run_dir}


def command_component_blueprints(args: argparse.Namespace) -> None:
    payload = {"components": COMPONENT_BLUEPRINTS, "generated_at": now_iso()}
    emit_payload(payload, args.output)


def emit_payload(payload: Any, output: str | None) -> None:
    if output:
        output_path = Path(output)
        if isinstance(payload, str):
            write_text(output_path, payload)
        else:
            write_json(output_path, payload)
        return
    if isinstance(payload, str):
        sys.stdout.write(payload)
        if not payload.endswith("\n"):
            sys.stdout.write("\n")
    else:
        sys.stdout.write(json.dumps(payload, indent=2) + "\n")


def command_intent_compile(args: argparse.Namespace) -> None:
    query = extract_query(args)
    context_text = Path(args.context_file).read_text() if args.context_file else ""
    payload = build_intent_contract(query, context_text=context_text)
    emit_payload(payload, args.output)


def command_create_ledger(args: argparse.Namespace) -> None:
    intent_payload = load_json(Path(args.intent_contract))
    contract = extract_contract(intent_payload)
    payload = build_task_ledger(contract, args.max_lanes)
    emit_payload(payload, args.output)


def command_merge_evidence(args: argparse.Namespace) -> None:
    intent_payload = load_json(Path(args.intent_contract))
    contract = extract_contract(intent_payload)
    ledger_payload = load_json(Path(args.task_ledger))
    task_ledger = ledger_payload.get("task_ledger", ledger_payload)
    evidence_records = load_evidence_records(Path(args.evidence_dir))
    payload = build_synthesis_state(contract, task_ledger, evidence_records)
    emit_payload(payload, args.output)


def command_build_artifact(args: argparse.Namespace) -> None:
    intent_payload = load_json(Path(args.intent_contract))
    contract = extract_contract(intent_payload)
    synthesis_payload = load_json(Path(args.synthesis_state))
    synthesis_state = synthesis_payload.get("synthesis_state", synthesis_payload)
    payload = build_artifact_payload(contract, synthesis_state, args.format)
    if args.output:
        output_path = Path(args.output)
        if args.format == "json":
            write_json(output_path, payload["final_artifact"])
        else:
            write_text(output_path, payload["final_artifact"])
        metadata_path = output_path.with_suffix(output_path.suffix + ".metadata.json") if output_path.suffix else output_path.with_name(output_path.name + ".metadata.json")
        write_json(metadata_path, {"artifact_metadata": payload["artifact_metadata"], "generated_at": payload["generated_at"]})
        emit_payload({"artifact_path": str(output_path), "metadata_path": str(metadata_path)}, None)
        return
    emit_payload(payload, None)


def command_quality_gate(args: argparse.Namespace) -> None:
    intent_payload = load_json(Path(args.intent_contract))
    contract = extract_contract(intent_payload)
    synthesis_payload = load_json(Path(args.synthesis_state))
    synthesis_state = synthesis_payload.get("synthesis_state", synthesis_payload)
    artifact_text = read_artifact_text(Path(args.artifact)) if args.artifact else ""
    payload = run_quality_gate(contract, synthesis_state, artifact_text)
    emit_payload(payload, args.output)


def command_telemetry_snapshot(args: argparse.Namespace) -> None:
    intent_payload = load_json(Path(args.intent_contract))
    contract = extract_contract(intent_payload)
    ledger_payload = load_json(Path(args.task_ledger))
    task_ledger = ledger_payload.get("task_ledger", ledger_payload)
    synthesis_payload = load_json(Path(args.synthesis_state))
    synthesis_state = synthesis_payload.get("synthesis_state", synthesis_payload)
    quality_payload = load_json(Path(args.quality_report))
    quality_report = quality_payload.get("quality_report", quality_payload)
    artifact_metadata_payload = load_json(Path(args.artifact_metadata))
    artifact_metadata = artifact_metadata_payload.get("artifact_metadata", artifact_metadata_payload)
    payload = build_telemetry_snapshot(contract, task_ledger, synthesis_state, artifact_metadata, quality_report, run_id=args.run_id)
    emit_payload(payload, args.output)


def command_agent_team_brief(args: argparse.Namespace) -> None:
    intent_payload = load_json(Path(args.intent_contract))
    contract = extract_contract(intent_payload)
    ledger_payload = load_json(Path(args.task_ledger))
    task_ledger = ledger_payload.get("task_ledger", ledger_payload)
    payload = build_agent_team_brief(contract, task_ledger)
    emit_payload(payload, args.output)


def command_pipeline(args: argparse.Namespace) -> None:
    query = extract_query(args)
    context_text = Path(args.context_file).read_text() if args.context_file else ""
    init = init_run(Path(args.workspace), query)
    run_dir = init["run_dir"]
    run_id = init["run_id"]

    intent_payload = build_intent_contract(query, context_text=context_text)
    write_json(run_dir / "intent_contract.json", intent_payload)

    contract = extract_contract(intent_payload)
    ledger_payload = build_task_ledger(contract, args.max_lanes)
    write_json(run_dir / "task_ledger.json", ledger_payload)

    evidence_dir = Path(args.evidence_dir) if args.evidence_dir else run_dir / "evidence"
    synthesis_payload = build_synthesis_state(contract, ledger_payload["task_ledger"], load_evidence_records(evidence_dir))
    write_json(run_dir / "synthesis_state.json", synthesis_payload)

    artifact_payload = build_artifact_payload(contract, synthesis_payload["synthesis_state"], args.format)
    artifact_name = "final_artifact.json" if args.format == "json" else "final_artifact.md"
    artifact_path = run_dir / "artifacts" / artifact_name
    if args.format == "json":
        write_json(artifact_path, artifact_payload["final_artifact"])
    else:
        write_text(artifact_path, artifact_payload["final_artifact"])
    artifact_metadata_path = run_dir / "artifacts" / "final_artifact.metadata.json"
    write_json(artifact_metadata_path, {"artifact_metadata": artifact_payload["artifact_metadata"], "generated_at": artifact_payload["generated_at"]})

    quality_payload = run_quality_gate(contract, synthesis_payload["synthesis_state"], read_artifact_text(artifact_path))
    write_json(run_dir / "quality_report.json", quality_payload)

    team_brief_payload = build_agent_team_brief(contract, ledger_payload["task_ledger"])
    write_json(run_dir / "agent_team_brief.json", team_brief_payload)

    telemetry_payload = build_telemetry_snapshot(
        contract,
        ledger_payload["task_ledger"],
        synthesis_payload["synthesis_state"],
        artifact_payload["artifact_metadata"],
        quality_payload["quality_report"],
        run_id=run_id,
    )
    write_json(run_dir / "telemetry.json", telemetry_payload)

    manifest = {
        "run_id": run_id,
        "run_dir": str(run_dir),
        "intent_contract": str(run_dir / "intent_contract.json"),
        "task_ledger": str(run_dir / "task_ledger.json"),
        "synthesis_state": str(run_dir / "synthesis_state.json"),
        "artifact": str(artifact_path),
        "artifact_metadata": str(artifact_metadata_path),
        "quality_report": str(run_dir / "quality_report.json"),
        "agent_team_brief": str(run_dir / "agent_team_brief.json"),
        "telemetry": str(run_dir / "telemetry.json"),
    }
    write_json(run_dir / "manifest.json", manifest)
    emit_payload(manifest, args.output)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Uncommon Sense orchestration CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    component_parser = subparsers.add_parser("component-blueprints", help="Print the seven component blueprints derived from the design brief.")
    component_parser.add_argument("--output")
    component_parser.set_defaults(func=command_component_blueprints)

    intent_parser = subparsers.add_parser("intent-compile", help="Build an intent contract from a query.")
    intent_parser.add_argument("--query")
    intent_parser.add_argument("--query-file")
    intent_parser.add_argument("--context-file")
    intent_parser.add_argument("--output")
    intent_parser.set_defaults(func=command_intent_compile)

    ledger_parser = subparsers.add_parser("create-ledger", help="Create a task ledger from an intent contract.")
    ledger_parser.add_argument("--intent-contract", required=True)
    ledger_parser.add_argument("--max-lanes", type=int, default=5)
    ledger_parser.add_argument("--output")
    ledger_parser.set_defaults(func=command_create_ledger)

    merge_parser = subparsers.add_parser("merge-evidence", help="Merge evidence JSON files into synthesis state.")
    merge_parser.add_argument("--intent-contract", required=True)
    merge_parser.add_argument("--task-ledger", required=True)
    merge_parser.add_argument("--evidence-dir", required=True)
    merge_parser.add_argument("--output")
    merge_parser.set_defaults(func=command_merge_evidence)

    artifact_parser = subparsers.add_parser("build-artifact", help="Build the final artifact from synthesis state.")
    artifact_parser.add_argument("--intent-contract", required=True)
    artifact_parser.add_argument("--synthesis-state", required=True)
    artifact_parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    artifact_parser.add_argument("--output")
    artifact_parser.set_defaults(func=command_build_artifact)

    quality_parser = subparsers.add_parser("quality-gate", help="Score output against the intent contract.")
    quality_parser.add_argument("--intent-contract", required=True)
    quality_parser.add_argument("--synthesis-state", required=True)
    quality_parser.add_argument("--artifact")
    quality_parser.add_argument("--output")
    quality_parser.set_defaults(func=command_quality_gate)

    telemetry_parser = subparsers.add_parser("telemetry-snapshot", help="Build an audit log from orchestration artifacts.")
    telemetry_parser.add_argument("--intent-contract", required=True)
    telemetry_parser.add_argument("--task-ledger", required=True)
    telemetry_parser.add_argument("--synthesis-state", required=True)
    telemetry_parser.add_argument("--artifact-metadata", required=True)
    telemetry_parser.add_argument("--quality-report", required=True)
    telemetry_parser.add_argument("--run-id")
    telemetry_parser.add_argument("--output")
    telemetry_parser.set_defaults(func=command_telemetry_snapshot)

    team_parser = subparsers.add_parser("agent-team-brief", help="Generate a delegated team brief from the intent contract and task ledger.")
    team_parser.add_argument("--intent-contract", required=True)
    team_parser.add_argument("--task-ledger", required=True)
    team_parser.add_argument("--output")
    team_parser.set_defaults(func=command_agent_team_brief)

    pipeline_parser = subparsers.add_parser("pipeline", help="Run the end-to-end orchestration scaffold.")
    pipeline_parser.add_argument("--query")
    pipeline_parser.add_argument("--query-file")
    pipeline_parser.add_argument("--context-file")
    pipeline_parser.add_argument("--workspace", required=True)
    pipeline_parser.add_argument("--evidence-dir")
    pipeline_parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    pipeline_parser.add_argument("--max-lanes", type=int, default=5)
    pipeline_parser.add_argument("--output")
    pipeline_parser.set_defaults(func=command_pipeline)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
