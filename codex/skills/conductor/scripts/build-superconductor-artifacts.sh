#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: build-superconductor-artifacts.sh <repo-root> <run-id>" >&2
  exit 1
fi

REPO_ROOT="$(cd "$1" && pwd)"
RUN_ID="$2"
SKILL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE_DIR="$SKILL_ROOT/templates/superconductor"
TARGET_DIR="$REPO_ROOT/conductor/superconductor/$RUN_ID"
GENERATED_AT="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

render_template() {
  local template_path="$1"
  local target_path="$2"

  sed \
    -e "s/{{RUN_ID}}/$RUN_ID/g" \
    -e "s/{{GENERATED_AT}}/$GENERATED_AT/g" \
    "$template_path" > "$target_path"
}

mkdir -p "$TARGET_DIR"

for artifact in \
  superconductor.md \
  intent-alignment-report.md \
  docs-gap-report.md \
  question-pack.json \
  dependency-closure.json \
  sufficiency-report.json \
  worker-context-manifest.json \
  requirements-matrix.json
do
  render_template "$TEMPLATE_DIR/$artifact" "$TARGET_DIR/$artifact"
done

echo "Created superconductor artifacts in $TARGET_DIR"
