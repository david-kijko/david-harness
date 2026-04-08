#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 <input-markdown> <output-path>" >&2
  exit 1
fi

INPUT="$1"
OUTPUT="$2"

if [[ ! -f "$INPUT" ]]; then
  echo "Input file not found: $INPUT" >&2
  exit 1
fi

EXT="${OUTPUT##*.}"

case "$EXT" in
  md|markdown)
    cp "$INPUT" "$OUTPUT"
    ;;
  html|pdf|docx)
    if ! command -v pandoc >/dev/null 2>&1; then
      echo "pandoc is required to render .$EXT outputs" >&2
      exit 1
    fi
    pandoc "$INPUT" -o "$OUTPUT"
    ;;
  *)
    echo "Unsupported output format: .$EXT" >&2
    echo "Supported formats: .md .html .pdf .docx" >&2
    exit 1
    ;;
esac
