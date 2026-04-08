#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILDER="$SCRIPT_DIR/build-superconductor-artifacts.sh"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

RUN_ID="brownfield-alignment"

"$BUILDER" "$TMP_DIR" "$RUN_ID"

TARGET_DIR="$TMP_DIR/conductor/superconductor/$RUN_ID"

for required in \
  superconductor.md \
  intent-alignment-report.md \
  docs-gap-report.md \
  question-pack.json \
  dependency-closure.json \
  sufficiency-report.json \
  worker-context-manifest.json \
  requirements-matrix.json
do
  if [[ ! -f "$TARGET_DIR/$required" ]]; then
    echo "FAIL: missing artifact: $required" >&2
    exit 1
  fi
done

grep -q "$RUN_ID" "$TARGET_DIR/superconductor.md"
grep -q '"gut_checks"' "$TARGET_DIR/worker-context-manifest.json"
grep -q '"requirements"' "$TARGET_DIR/requirements-matrix.json"

echo "PASS: all superconductor artifacts created and validated"
