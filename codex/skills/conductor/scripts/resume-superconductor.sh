#!/usr/bin/env bash
# resume-superconductor.sh — Reads the current superconductor state and
# outputs exactly what the agent should do next.
#
# The agent MUST run this at the START of every /conductor:superconductor
# invocation. It replaces the "figure out where we are" improvisation
# with a deterministic read of the matrix.
#
# Usage: resume-superconductor.sh <repo-root> [run-id]
#
# Output: JSON object with next_action, stage, incomplete_tracks, etc.

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: resume-superconductor.sh <repo-root> [run-id]" >&2
  exit 2
fi

REPO_ROOT="$(cd "$1" && pwd)"
RUN_ID="${2:-}"
SC_DIR="$REPO_ROOT/conductor/superconductor"

# Find the run
if [[ -z "$RUN_ID" ]]; then
  MATRIX=$(find "$SC_DIR" -name "requirements-matrix.json" -type f 2>/dev/null | head -n 1)
  if [[ -z "$MATRIX" ]]; then
    echo '{"next_action":"start_fresh","stage":0,"message":"No existing run found. Start from Stage 1.","incomplete_tracks":[],"verified":0,"total":0}'
    exit 0
  fi
else
  MATRIX="$SC_DIR/$RUN_ID/requirements-matrix.json"
  if [[ ! -f "$MATRIX" ]]; then
    echo '{"next_action":"start_fresh","stage":0,"message":"Run '"$RUN_ID"' not found. Start from Stage 1.","incomplete_tracks":[],"verified":0,"total":0}'
    exit 0
  fi
fi

# Parse with Python
if command -v python3 &>/dev/null; then
  python3 - "$MATRIX" "$REPO_ROOT" <<'PY'
import json, sys, os
from pathlib import Path

matrix_path = sys.argv[1]
repo_root = sys.argv[2]
data = json.loads(open(matrix_path).read())

reqs = data.get("requirements", [])
total = len(reqs)
stage = data.get("pipeline_stage", 0)

by_status = {}
for r in reqs:
    s = r.get("status", "pending")
    by_status[s] = by_status.get(s, 0) + 1

verified = by_status.get("verified", 0)
implemented = by_status.get("implemented", 0)
in_track = by_status.get("in_track", by_status.get("in-track", 0))
pending = by_status.get("pending", 0)

# Find incomplete tracks
tracks_dir = Path(repo_root) / "conductor" / "tracks"
incomplete_tracks = []
if tracks_dir.exists():
    for track_dir in sorted(tracks_dir.iterdir()):
        plan = track_dir / "plan.md"
        if plan.exists():
            content = plan.read_text()
            pending_tasks = content.count("- [ ]")
            in_progress = content.count("- [~]")
            completed = content.count("- [x]")
            if pending_tasks > 0 or in_progress > 0:
                incomplete_tracks.append({
                    "track_id": track_dir.name,
                    "pending_tasks": pending_tasks,
                    "in_progress_tasks": in_progress,
                    "completed_tasks": completed
                })

# Determine next action
if total == 0:
    next_action = "start_fresh"
    message = "Empty matrix. Start from Stage 1: parse requirements."
elif pending > 0:
    next_action = "decompose"
    message = f"{pending} requirements not yet assigned to tracks. Run Stage 6."
elif stage < 6:
    next_action = f"resume_stage_{stage}"
    message = f"Resume at Stage {stage}. Investigation/alignment not yet complete."
elif in_track > 0 and len(incomplete_tracks) > 0:
    next_action = "fan_out_workers"
    track_names = [t["track_id"] for t in incomplete_tracks[:5]]
    message = f"{in_track} requirements in-track. Fan out workers for: {', '.join(track_names)}"
elif implemented > 0:
    next_action = "run_reviews"
    message = f"{implemented} requirements implemented but not verified. Run reviews."
elif verified == total:
    next_action = "complete"
    message = "All requirements verified. Run is complete."
else:
    next_action = "investigate"
    message = "Ambiguous state. Check matrix manually."

result = {
    "next_action": next_action,
    "stage": stage,
    "message": message,
    "run_id": data.get("run_id", "unknown"),
    "total": total,
    "verified": verified,
    "implemented": implemented,
    "in_track": in_track,
    "pending": pending,
    "incomplete_tracks": incomplete_tracks[:10],
    "matrix_path": matrix_path
}

print(json.dumps(result, indent=2))
PY
elif command -v node &>/dev/null; then
  echo '{"error":"Python not available; node fallback not implemented for resume. Install python3."}'
  exit 2
else
  echo '{"error":"Neither python3 nor node available"}'
  exit 2
fi
