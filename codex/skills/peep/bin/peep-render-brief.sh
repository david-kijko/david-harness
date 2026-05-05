#!/usr/bin/env bash
set -euo pipefail

fail() {
  printf 'peep-render-brief: FAIL: %s\n' "$*" >&2
  exit 1
}

usage() {
  cat >&2 <<'USAGE'
Usage: peep-render-brief.sh --brief <path> --out <path>
USAGE
  exit 1
}

brief=""
out=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --brief)
      [[ $# -ge 2 ]] || fail "--brief requires a path"
      brief="$2"
      shift 2
      ;;
    --out)
      [[ $# -ge 2 ]] || fail "--out requires a path"
      out="$2"
      shift 2
      ;;
    -h|--help)
      usage
      ;;
    *)
      fail "unknown argument: $1"
      ;;
  esac
done

[[ -n "$brief" ]] || usage
[[ -n "$out" ]] || usage
[[ -f "$brief" ]] || fail "brief does not exist: $brief"
[[ -s "$brief" ]] || fail "brief is empty: $brief"
[[ "$brief" == *.brief.md ]] || fail "brief path must end in .brief.md: $brief"
[[ "$out" == *.png ]] || fail "out path must end in .png: $out"

out_parent=$(dirname -- "$out")
[[ -d "$out_parent" ]] || fail "out parent dir does not exist: $out_parent"

brief_abs=$(realpath -- "$brief")
out_abs=$(realpath -m -- "$out")
out_parent_abs=$(realpath -- "$out_parent")

if [[ -e "$out_abs" && ! -f "$out_abs" ]]; then
  fail "out path exists but is not a regular file: $out_abs"
fi

dispatch_brief=$(mktemp /tmp/peep-render-brief.XXXXXX.md)
dispatch_log=$(mktemp /tmp/peep-render-brief.XXXXXX.log)
cleanup() {
  rm -f "$dispatch_brief" "$dispatch_log"
}
trap cleanup EXIT

cat > "$dispatch_brief" <<BRIEF
file_create

Use \$imagegen to render the peep mental-model diagram.

Read the brief at: $brief_abs
Render the diagram it specifies.
Save/copy the final selected PNG image exactly to: $out_abs

Execution constraints:
- Use Codex's built-in \$imagegen / image_gen tool through the existing imagegen skill.
- Do not use browser automation, Playwright, ChatGPT web UI, OpenAI SDK/API scripts, or a custom runner.
- If the generated file lands under \$CODEX_HOME/generated_images first, copy the final selected image to the requested output path.
- The output path's parent already exists: $out_parent_abs
- Do not leave the requested output path missing.

Required verification in your final output:
- Print a line starting with \`output:\` containing the generated image path.
- Run \`file\` and byte-size inspection on the generated image.
- Print a line starting with \`contents:\` containing path, byte size, image format, width, and height.
- Do not claim completion without those literal lines.
BRIEF

if ! COMPLETION_GUARD_TASK_TYPE=file_create \
  HEPHAESTUS_MODEL="${HEPHAESTUS_MODEL:-gpt-5.5}" \
  HEPHAESTUS_REASONING_EFFORT="${HEPHAESTUS_REASONING_EFFORT:-high}" \
  hephaestus --file "$dispatch_brief" --dir "$out_parent_abs" --dangerous >"$dispatch_log" 2>&1; then
  tail_output=$(tail -40 "$dispatch_log" || true)
  fail "imagegen dispatch failed; tail: $tail_output"
fi

[[ -f "$out_abs" ]] || fail "output file was not created: $out_abs"
bytes=$(wc -c < "$out_abs" | tr -d '[:space:]')
[[ "$bytes" =~ ^[0-9]+$ ]] || fail "could not determine output size: $out_abs"
if (( bytes < 1024 )); then
  fail "output file too small: path=$out_abs bytes=$bytes"
fi
file_report=$(file -b -- "$out_abs")
if [[ "$file_report" != *"PNG image"* ]]; then
  fail "output is not a PNG image: path=$out_abs file=$file_report"
fi

printf 'peep-render-brief: ok path=%s bytes=%s\n' "$out_abs" "$bytes"
