#!/usr/bin/env bash
set -euo pipefail

upgrade=0
for arg in "$@"; do
  case "$arg" in
    --upgrade)
      upgrade=1
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      echo "Usage: $(basename "$0") [--upgrade]" >&2
      exit 2
      ;;
  esac
done

if ! command -v agent-browser >/dev/null 2>&1 || [[ "$upgrade" -eq 1 ]]; then
  npm install -g agent-browser@latest
fi

binary_path="$(command -v agent-browser)"
version="$(agent-browser --version)"

echo "agent-browser binary: $binary_path"
echo "agent-browser version: $version"

if [[ "$(uname -s)" == "Linux" ]]; then
  agent-browser install
else
  agent-browser install
fi

tmpdir="$(mktemp -d)"
snapshot_file="$tmpdir/snapshot.txt"

cleanup() {
  if command -v agent-browser >/dev/null 2>&1; then
    agent-browser close >/dev/null 2>&1 || true
  fi
  rm -rf "$tmpdir"
}

trap cleanup EXIT

agent-browser open https://example.com >/dev/null
agent-browser wait --load domcontentloaded >/dev/null
agent-browser snapshot -i -C -c >"$snapshot_file"
agent-browser close >/dev/null

if [[ ! -s "$snapshot_file" ]]; then
  echo "Smoke test failed: snapshot output was empty" >&2
  exit 1
fi

echo "Smoke test passed: captured $(wc -c <"$snapshot_file") bytes of snapshot output"
