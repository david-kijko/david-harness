#!/usr/bin/env python3
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path
from typing import Any

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


class PatchApplicationError(Exception):
    pass


def load_json(path: str) -> dict[str, Any]:
    if path == "-":
        return json.load(sys.stdin)
    return json.loads(Path(path).read_text(encoding="utf-8"))


def normalize_text(text: str) -> str:
    if not text.endswith("\n"):
        return text + "\n"
    return text


def split_lines(text: str) -> list[str]:
    return normalize_text(text).splitlines(keepends=True)


def join_lines(lines: list[str]) -> str:
    return "".join(lines)


def resolve_anchor(lines: list[str], target_section: str) -> tuple[str, int, int]:
    if target_section == "BOF":
        return ("line", 0, 0)
    if target_section == "EOF":
        return ("line", len(lines), len(lines))

    stripped_target = target_section.strip()

    for index, line in enumerate(lines):
        match = HEADING_RE.match(line.rstrip("\n"))
        if match and match.group(2).strip() == stripped_target:
            level = len(match.group(1))
            end = len(lines)
            for cursor in range(index + 1, len(lines)):
                next_match = HEADING_RE.match(lines[cursor].rstrip("\n"))
                if next_match and len(next_match.group(1)) <= level:
                    end = cursor
                    break
            return ("section", index, end)

    for index, line in enumerate(lines):
        if line.rstrip("\n") == stripped_target:
            return ("line", index, index + 1)

    raise PatchApplicationError(f"could not find target_section {target_section!r}")


def insert_after(lines: list[str], target_section: str, content: str) -> list[str]:
    anchor_type, start, end = resolve_anchor(lines, target_section)
    insert_at = end if anchor_type == "line" and target_section == "EOF" else start + 1 if anchor_type == "section" else end
    new_lines = split_lines(content)
    return lines[:insert_at] + new_lines + lines[insert_at:]


def replace_target(lines: list[str], target_section: str, content: str) -> list[str]:
    _, start, end = resolve_anchor(lines, target_section)
    return lines[:start] + split_lines(content) + lines[end:]


def delete_target(lines: list[str], target_section: str) -> list[str]:
    _, start, end = resolve_anchor(lines, target_section)
    return lines[:start] + lines[end:]


def apply_edit(current_text: str, edit: dict[str, Any]) -> str:
    op = edit["op"]
    content = edit.get("content", "")
    target_section = edit["target_section"]

    if op == "create":
        return normalize_text(content)

    lines = split_lines(current_text)
    if op == "insert_after":
        return join_lines(insert_after(lines, target_section, content))
    if op == "replace":
        return join_lines(replace_target(lines, target_section, content))
    if op == "delete":
        return join_lines(delete_target(lines, target_section))
    raise PatchApplicationError(f"unsupported edit op: {op}")


def generate_diff(path: str, before: str, after: str) -> str:
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=path,
            tofile=path,
        )
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Translate a Trace2Skill patch into a unified diff or write it to disk.")
    parser.add_argument("patch", help="Path to the patch JSON file, or - to read from stdin")
    parser.add_argument("--skill-dir", default=".", help="Target skill directory (default: current directory)")
    parser.add_argument("--write", action="store_true", help="Write the patch result to disk instead of diff-only output")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        patch = load_json(args.patch)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    skill_dir = Path(args.skill_dir).resolve()
    updates: dict[str, tuple[str, str]] = {}

    for entry in patch.get("new_files", []):
        rel_path = entry["path"]
        before = ""
        after = normalize_text(entry["content"])
        updates[rel_path] = (before, after)

    for edit in patch.get("edits", []):
        rel_path = edit["file"]
        disk_path = skill_dir / rel_path
        if rel_path in updates:
            current_text = updates[rel_path][1]
        elif disk_path.exists():
            current_text = disk_path.read_text(encoding="utf-8")
        else:
            current_text = ""

        before = current_text
        after = apply_edit(current_text, edit)
        updates[rel_path] = (before if rel_path not in updates else updates[rel_path][0], after)

    diffs: list[str] = []
    for rel_path in sorted(updates):
        before, after = updates[rel_path]
        diff = generate_diff(rel_path, before, after)
        if diff:
            diffs.append(diff)
            if args.write:
                destination = skill_dir / rel_path
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(after, encoding="utf-8")

    if diffs:
        sys.stdout.write("\n".join(diffs))
    else:
        print("No changes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
