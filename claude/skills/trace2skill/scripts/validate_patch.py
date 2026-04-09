#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ALLOWED_OUTCOMES = {"success", "failure", "ambiguous"}
ALLOWED_ANALYST_TYPES = {"error", "success"}
ALLOWED_CONFIDENCE = {"high", "medium", "low"}
ALLOWED_PRIORITIES = {"critical", "recommended", "nice-to-have"}
ALLOWED_OPS = {"insert_after", "replace", "delete", "create"}
ALLOWED_ROOT_CAUSES = {
    "wrong-tool-choice",
    "missing-verification",
    "incorrect-reasoning",
    "misunderstood-intent",
    "environment-mismatch",
    "silent-data-corruption",
    "context-window-loss",
    "premature-delivery",
    "other",
}
REFERENCE_LINK_RE = re.compile(r"\b(?:\./)?(references/[A-Za-z0-9._/-]+\.md)\b")
ABSOLUTE_PATH_RE = re.compile(r"(?:^|[^A-Za-z0-9._-])(/(?:home|Users|tmp|var|etc)/[^\s`]+)")
WORD_RE = re.compile(r"\b\S+\b")


class ValidationError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def load_json(path: str) -> dict[str, Any]:
    if path == "-":
        return json.load(sys.stdin)
    return json.loads(Path(path).read_text(encoding="utf-8"))


def word_count(text: str) -> int:
    return len(WORD_RE.findall(text))


def token_estimate(text: str) -> int:
    return len(text.split())


def files_in_tree(root: Path) -> set[str]:
    if not root.exists():
        return set()
    return {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    }


def ensure_string(value: Any, field_name: str) -> str:
    require(isinstance(value, str), f"{field_name} must be a string")
    require(bool(value.strip()), f"{field_name} must not be empty")
    return value


def validate_top_level(patch: dict[str, Any]) -> None:
    required_keys = {
        "$schema",
        "trace_id",
        "outcome",
        "analyst_type",
        "confidence",
        "root_cause_label",
        "phase",
        "reasoning",
        "sops",
        "edits",
        "new_files",
    }
    missing = sorted(required_keys - set(patch))
    require(not missing, f"missing required top-level keys: {', '.join(missing)}")
    require(patch["$schema"] == "trace2skill-patch-v1", "$schema must equal trace2skill-patch-v1")
    ensure_string(patch["trace_id"], "trace_id")
    require(patch["outcome"] in ALLOWED_OUTCOMES, "outcome must be success, failure, or ambiguous")
    require(patch["analyst_type"] in ALLOWED_ANALYST_TYPES, "analyst_type must be error or success")
    require(patch["confidence"] in ALLOWED_CONFIDENCE, "confidence must be high, medium, or low")
    ensure_string(patch["phase"], "phase")
    reasoning = ensure_string(patch["reasoning"], "reasoning")
    reasoning_words = word_count(reasoning)
    require(100 <= reasoning_words <= 500, "reasoning must be between 100 and 500 words")

    if patch["analyst_type"] == "success":
        require(patch["root_cause_label"] is None, "success patches must set root_cause_label to null")
    else:
        require(
            isinstance(patch["root_cause_label"], str) and patch["root_cause_label"] in ALLOWED_ROOT_CAUSES,
            "error patches must use a root_cause_label from the allowed taxonomy",
        )

    require(isinstance(patch["sops"], list), "sops must be a list")
    require(isinstance(patch["edits"], list), "edits must be a list")
    require(isinstance(patch["new_files"], list), "new_files must be a list")
    require(patch["sops"], "sops must not be empty")


def validate_sops(patch: dict[str, Any]) -> None:
    seen_ids: set[str] = set()
    for index, sop in enumerate(patch["sops"]):
        require(isinstance(sop, dict), f"sops[{index}] must be an object")
        sop_id = ensure_string(sop.get("id"), f"sops[{index}].id")
        require(sop_id not in seen_ids, f"duplicate sop.id detected: {sop_id}")
        seen_ids.add(sop_id)
        ensure_string(sop.get("when"), f"sops[{index}].when")
        ensure_string(sop.get("what"), f"sops[{index}].what")
        ensure_string(sop.get("why"), f"sops[{index}].why")
        require(sop.get("source_type") in ALLOWED_ANALYST_TYPES, f"sops[{index}].source_type is invalid")
        require(sop.get("priority") in ALLOWED_PRIORITIES, f"sops[{index}].priority is invalid")


def validate_new_files(patch: dict[str, Any]) -> set[str]:
    created: set[str] = set()
    for index, entry in enumerate(patch["new_files"]):
        require(isinstance(entry, dict), f"new_files[{index}] must be an object")
        path = ensure_string(entry.get("path"), f"new_files[{index}].path")
        ensure_string(entry.get("content"), f"new_files[{index}].content")
        require(path not in created, f"duplicate new_files path: {path}")
        created.add(path)
    return created


def validate_edits(patch: dict[str, Any], target_root: Path, created_paths: set[str]) -> None:
    existing_files = files_in_tree(target_root)
    pending_known_files = set(existing_files) | set(created_paths)
    seen_targets: set[tuple[str, str]] = set()

    for index, edit in enumerate(patch["edits"]):
        require(isinstance(edit, dict), f"edits[{index}] must be an object")
        file_name = ensure_string(edit.get("file"), f"edits[{index}].file")
        op = edit.get("op")
        require(op in ALLOWED_OPS, f"edits[{index}].op is invalid")
        target_section = ensure_string(edit.get("target_section"), f"edits[{index}].target_section")
        content = edit.get("content", "")
        require(isinstance(content, str), f"edits[{index}].content must be a string")

        if op == "create":
            pending_known_files.add(file_name)
        require(
            file_name in pending_known_files,
            f"edits[{index}].file must reference an existing file or one created in the same patch: {file_name}",
        )

        target_key = (file_name, target_section)
        require(target_key not in seen_targets, f"possible overlapping edits on {file_name!r} at {target_section!r}")
        seen_targets.add(target_key)

        require(token_estimate(content) <= 2000, f"edits[{index}].content exceeds the 2000-token limit")

        if ABSOLUTE_PATH_RE.search(content):
            raise ValidationError(
                f"edits[{index}].content appears to contain an absolute path copied from a trace; replace it with a generalized description"
            )

        for linked_path in REFERENCE_LINK_RE.findall(content):
            require(
                linked_path in pending_known_files,
                f"edits[{index}].content links to {linked_path}, but that file does not exist or is not created in new_files",
            )


def validate_patch(patch: dict[str, Any], target_root: Path) -> dict[str, Any]:
    validate_top_level(patch)
    validate_sops(patch)
    created_paths = validate_new_files(patch)
    validate_edits(patch, target_root, created_paths)
    return {
        "status": "ok",
        "trace_id": patch["trace_id"],
        "sop_count": len(patch["sops"]),
        "edit_count": len(patch["edits"]),
        "new_file_count": len(patch["new_files"]),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate a Trace2Skill patch against the v1 contract and guardrails.")
    parser.add_argument("patch", help="Path to the patch JSON file, or - to read from stdin")
    parser.add_argument(
        "--target-dir",
        default=".",
        help="Target skill directory used for referential-integrity checks (default: current directory)",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print the validation result")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        patch = load_json(args.patch)
        result = validate_patch(patch, Path(args.target_dir).resolve())
    except (json.JSONDecodeError, OSError, ValidationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.pretty:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
