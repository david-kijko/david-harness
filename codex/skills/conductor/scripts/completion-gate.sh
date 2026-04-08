#!/usr/bin/env bash
# completion-gate.sh — Hard enforcement gate for superconductor runs.
#
# Reads requirements-matrix.json and exits non-zero if ANY requirement
# is not yet verified. The agent MUST run this after every worker wave
# and MUST NOT declare completion if it exits non-zero.
#
# Usage: completion-gate.sh <repo-root> [run-id]
#   If run-id is omitted, finds the most recent run.
#
# Exit codes:
#   0 = ALL requirements verified. Run is complete.
#   1 = Work remains. Agent must continue or re-invoke.
#   2 = No matrix found or parse error.

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: completion-gate.sh <repo-root> [run-id]" >&2
  exit 2
fi

REPO_ROOT="$(cd "$1" && pwd)"
RUN_ID="${2:-}"
SC_DIR="$REPO_ROOT/conductor/superconductor"

# Find the run
if [[ -z "$RUN_ID" ]]; then
  # Pick the most recently modified run
  MATRIX=$(find "$SC_DIR" -name "requirements-matrix.json" -type f 2>/dev/null | head -n 1)
  if [[ -z "$MATRIX" ]]; then
    echo "ERROR: No requirements-matrix.json found under $SC_DIR" >&2
    exit 2
  fi
else
  MATRIX="$SC_DIR/$RUN_ID/requirements-matrix.json"
  if [[ ! -f "$MATRIX" ]]; then
    echo "ERROR: $MATRIX does not exist" >&2
    exit 2
  fi
fi

RUN_DIR="$(dirname "$MATRIX")"
ACTUAL_RUN_ID="$(basename "$RUN_DIR")"

# Parse the matrix with Python (available everywhere) or node
if command -v python3 &>/dev/null; then
  RESULT=$(python3 - "$MATRIX" <<'PY'
import json, sys
path = sys.argv[1]
data = json.loads(open(path).read())
reqs = data.get("requirements", [])
total = len(reqs)
by_status = {}
for r in reqs:
    s = r.get("status", "pending")
    by_status[s] = by_status.get(s, 0) + 1

verified = by_status.get("verified", 0)
implemented = by_status.get("implemented", 0)
in_track = by_status.get("in_track", by_status.get("in-track", 0))
pending = by_status.get("pending", 0)
stage = data.get("pipeline_stage", "unknown")

print(f"RUN_ID={data.get('run_id','unknown')}")
print(f"STAGE={stage}")
print(f"TOTAL={total}")
print(f"VERIFIED={verified}")
print(f"IMPLEMENTED={implemented}")
print(f"IN_TRACK={in_track}")
print(f"PENDING={pending}")
print(f"REMAINING={total - verified}")
PY
  )
elif command -v node &>/dev/null; then
  RESULT=$(node -e "
    const d=JSON.parse(require('fs').readFileSync('$MATRIX','utf8'));
    const r=d.requirements||[];const t=r.length;
    const c={};r.forEach(x=>{const s=x.status||'pending';c[s]=(c[s]||0)+1});
    const v=c.verified||0;const i=c.implemented||0;
    const it=c['in-track']||c['in_track']||0;const p=c.pending||0;
    console.log('RUN_ID='+(d.run_id||'unknown'));
    console.log('STAGE='+(d.pipeline_stage||'unknown'));
    console.log('TOTAL='+t);console.log('VERIFIED='+v);
    console.log('IMPLEMENTED='+i);console.log('IN_TRACK='+it);
    console.log('PENDING='+p);console.log('REMAINING='+(t-v));
  ")
else
  echo "ERROR: Neither python3 nor node available" >&2
  exit 2
fi

# Parse results
eval "$RESULT"

echo "╔══════════════════════════════════════════════╗"
echo "║     SUPERCONDUCTOR COMPLETION GATE           ║"
echo "╠══════════════════════════════════════════════╣"
echo "║ Run:         $RUN_ID"
echo "║ Stage:       $STAGE"
echo "║ Total:       $TOTAL requirements"
echo "║ Verified:    $VERIFIED"
echo "║ Implemented: $IMPLEMENTED"
echo "║ In-Track:    $IN_TRACK"
echo "║ Pending:     $PENDING"
echo "║ Remaining:   $REMAINING"
echo "╠══════════════════════════════════════════════╣"

if [[ "$REMAINING" -eq 0 ]]; then
  echo "║ ✅ GATE PASSED — All requirements verified   ║"
  echo "╚══════════════════════════════════════════════╝"
  exit 0
else
  PCT=$((VERIFIED * 100 / TOTAL))
  echo "║ ❌ GATE FAILED — $REMAINING of $TOTAL remain ($PCT% done)"
  echo "║                                              ║"
  echo "║ DO NOT declare completion.                   ║"
  echo "║ Continue to the next worker wave or          ║"
  echo "║ re-invoke /conductor:superconductor          ║"
  echo "╚══════════════════════════════════════════════╝"
  exit 1
fi
