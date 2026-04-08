#!/usr/bin/env bash
# superconductor-driver.sh — External loop driver for superconductor.
#
# This script IS the enforcement mechanism. It takes the loop control
# away from the agent and runs it from bash. The agent cannot decide
# to stop early — this script decides.
#
# Architecture:
#   1. Run resume-superconductor.sh to determine current state
#   2. If work remains, invoke `codex exec` with a focused prompt
#      for the next incomplete track(s)
#   3. After the agent finishes, run completion-gate.sh
#   4. If gate fails, loop back to step 1
#   5. Exit when gate passes or max iterations reached
#
# Usage:
#   superconductor-driver.sh <repo-root> [options]
#
# Options:
#   --run-id <id>         Target a specific superconductor run
#   --max-waves <n>       Maximum worker waves before stopping (default: 50)
#   --tracks-per-wave <n> How many tracks to assign per codex invocation (default: 3)
#   --codex-cmd <cmd>     Codex command (default: "codex exec --yolo")
#   --dry-run             Print what would be done without invoking codex
#   --setup               Run stages 1-7 (intake through track generation) first
#
# Prerequisites:
#   - codex CLI installed and authenticated
#   - python3 available
#   - Conductor setup completed (/conductor:setup)
#   - Requirements source available (for --setup mode)
#
# Exit codes:
#   0 = All requirements verified (gate passed)
#   1 = Max waves reached, work remains
#   2 = Error (no matrix, parse failure, codex not found)

set -euo pipefail

# ─── Defaults ───────────────────────────────────────────────────
MAX_WAVES=50
TRACKS_PER_WAVE=3
CODEX_CMD="codex exec --yolo"
DRY_RUN=false
SETUP_MODE=false
RUN_ID=""
REQ_SOURCE=""

# ─── Parse args ─────────────────────────────────────────────────
if [[ $# -lt 1 ]]; then
  cat >&2 <<'USAGE'
usage: superconductor-driver.sh <repo-root> [options]

Options:
  --run-id <id>         Target a specific superconductor run
  --max-waves <n>       Maximum worker waves (default: 50)
  --tracks-per-wave <n> Tracks per codex invocation (default: 3)
  --codex-cmd <cmd>     Codex command (default: "codex exec --yolo")
  --dry-run             Print actions without invoking codex
  --setup <source>      Run stages 1-7 first with given requirements source

Exit codes:
  0 = All requirements verified
  1 = Max waves reached, work remains
  2 = Error
USAGE
  exit 2
fi

REPO_ROOT="$(cd "$1" && pwd)"
shift

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id)      RUN_ID="$2"; shift 2 ;;
    --max-waves)   MAX_WAVES="$2"; shift 2 ;;
    --tracks-per-wave) TRACKS_PER_WAVE="$2"; shift 2 ;;
    --codex-cmd)   CODEX_CMD="$2"; shift 2 ;;
    --dry-run)     DRY_RUN=true; shift ;;
    --setup)       SETUP_MODE=true; REQ_SOURCE="$2"; shift 2 ;;
    *)             echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RESUME_SCRIPT="$SCRIPT_DIR/resume-superconductor.sh"
GATE_SCRIPT="$SCRIPT_DIR/completion-gate.sh"
LOG_DIR="$REPO_ROOT/conductor/superconductor/.driver-logs"
mkdir -p "$LOG_DIR"

# ─── Verify prerequisites ──────────────────────────────────────
if ! command -v codex &>/dev/null && [[ "$DRY_RUN" == "false" ]]; then
  echo "ERROR: codex CLI not found in PATH" >&2
  exit 2
fi

if ! command -v python3 &>/dev/null; then
  echo "ERROR: python3 not found in PATH" >&2
  exit 2
fi

if [[ ! -x "$RESUME_SCRIPT" ]]; then
  echo "ERROR: resume-superconductor.sh not found at $RESUME_SCRIPT" >&2
  exit 2
fi

if [[ ! -x "$GATE_SCRIPT" ]]; then
  echo "ERROR: completion-gate.sh not found at $GATE_SCRIPT" >&2
  exit 2
fi

# ─── Helper: timestamp ─────────────────────────────────────────
ts() { date '+%Y-%m-%d %H:%M:%S'; }

# ─── Helper: log ────────────────────────────────────────────────
log() {
  echo "[$(ts)] $*" | tee -a "$LOG_DIR/driver.log"
}

# ─── Helper: invoke codex ──────────────────────────────────────
invoke_codex() {
  local prompt="$1"
  local wave_num="$2"
  local log_file="$LOG_DIR/wave-${wave_num}.log"

  if [[ "$DRY_RUN" == "true" ]]; then
    log "[DRY RUN] Would invoke codex with prompt:"
    log "  ${prompt:0:200}..."
    return 0
  fi

  log "Invoking codex (wave $wave_num)..."
  log "Prompt: ${prompt:0:200}..."

  # Use codex exec with the prompt, working from repo root
  # --output-last-message captures the agent's final message for logging
  local output_file="$LOG_DIR/wave-${wave_num}-output.md"

  set +e
  $CODEX_CMD \
    --cd "$REPO_ROOT" \
    -o "$output_file" \
    "$prompt" \
    2>&1 | tee "$log_file"
  local codex_exit=$?
  set -e

  if [[ $codex_exit -ne 0 ]]; then
    log "WARNING: codex exited with code $codex_exit (wave $wave_num)"
  fi

  return 0
}

# ─── Helper: run gate ──────────────────────────────────────────
run_gate() {
  local run_id_arg=""
  if [[ -n "$RUN_ID" ]]; then
    run_id_arg="$RUN_ID"
  fi

  set +e
  "$GATE_SCRIPT" "$REPO_ROOT" $run_id_arg 2>&1 | tee -a "$LOG_DIR/driver.log"
  local gate_exit=${PIPESTATUS[0]}
  set -e

  return $gate_exit
}

# ─── Helper: get resume state as JSON ──────────────────────────
get_resume_state() {
  local run_id_arg=""
  if [[ -n "$RUN_ID" ]]; then
    run_id_arg="$RUN_ID"
  fi

  "$RESUME_SCRIPT" "$REPO_ROOT" $run_id_arg 2>/dev/null
}

# ─── Helper: build worker prompt for tracks ────────────────────
build_worker_prompt() {
  local tracks_json="$1"
  local wave_num="$2"
  local total="$3"
  local verified="$4"

  # Extract track IDs from JSON array
  local track_ids
  track_ids=$(echo "$tracks_json" | python3 -c "
import json, sys
tracks = json.load(sys.stdin)
for t in tracks:
    print(t['track_id'])
" 2>/dev/null || echo "")

  if [[ -z "$track_ids" ]]; then
    echo ""
    return
  fi

  # Build a focused prompt that tells the agent EXACTLY what to do
  local track_list=""
  local track_specs=""
  while IFS= read -r tid; do
    track_list="${track_list}  - ${tid}\n"
    local spec_file="$REPO_ROOT/conductor/tracks/$tid/spec.md"
    local plan_file="$REPO_ROOT/conductor/tracks/$tid/plan.md"
    if [[ -f "$spec_file" && -f "$plan_file" ]]; then
      track_specs="${track_specs}

### Track: ${tid}
Spec: conductor/tracks/${tid}/spec.md
Plan: conductor/tracks/${tid}/plan.md
Read both files. Complete ALL tasks marked [ ] in the plan."
    fi
  done <<< "$track_ids"

  cat <<PROMPT
You are executing wave ${wave_num} of a superconductor run. ${verified} of ${total} requirements are verified.

YOUR ASSIGNMENT: Implement the following track(s) to completion:
$(echo -e "$track_list")

FOR EACH TRACK:
1. Read conductor/tracks/<track_id>/spec.md and conductor/tracks/<track_id>/plan.md
2. Read conductor/workflow.md for the task lifecycle
3. For EVERY task marked [ ] in the plan:
   a. Write failing tests (if TDD workflow)
   b. Implement the code
   c. Run tests to verify
   d. Mark the task [x] in plan.md with commit SHA
   e. Commit with conventional message
4. After ALL tasks in a track are [x], update conductor/tracks/<track_id>/metadata.json status to "complete"

AFTER completing all assigned tracks:
1. Update conductor/superconductor/*/requirements-matrix.json:
   - Set status to "verified" for each requirement covered by the completed tracks
   - Add evidence array with test/build verification commands you ran
2. Commit all conductor state changes

RULES:
- Do NOT stop after one track. Complete ALL assigned tracks.
- Do NOT skip tasks. Every [ ] must become [x].
- Do NOT declare "honest status" and stop. Finish the work.
- If a task is blocked, document why in the plan and move to the next task.
${track_specs}
PROMPT
}

# ─── SETUP MODE: Stages 1-7 ────────────────────────────────────
if [[ "$SETUP_MODE" == "true" ]]; then
  log "═══════════════════════════════════════════════"
  log "SUPERCONDUCTOR DRIVER — SETUP MODE"
  log "Repository: $REPO_ROOT"
  log "Requirements source: $REQ_SOURCE"
  log "═══════════════════════════════════════════════"

  setup_prompt="Run /conductor:superconductor with requirements source: ${REQ_SOURCE}

Execute Stages 1 through 7 ONLY (Intake through Track Generation):
- Stage 1: Parse requirements into requirements-matrix.json
- Stage 2: Intent alignment
- Stage 3: CGC/code investigation
- Stage 4: Closure
- Stage 5: Sufficiency gate
- Stage 6: Decompose into domain tracks
- Stage 7: Generate all track directories with spec.md and plan.md

STOP after Stage 7. Do NOT start Stage 8 (worker fan-out).
The driver script will handle worker execution.

After Stage 7, verify:
- requirements-matrix.json has zero pending requirements (all in-track or better)
- Every track in the matrix has a directory under conductor/tracks/ with spec.md and plan.md
- conductor/tracks.md is updated with all tracks"

  invoke_codex "$setup_prompt" "setup"

  log "Setup complete. Switching to worker loop."
  log ""
fi

# ─── MAIN LOOP ──────────────────────────────────────────────────
log "═══════════════════════════════════════════════"
log "SUPERCONDUCTOR DRIVER — WORKER LOOP"
log "Repository:       $REPO_ROOT"
log "Max waves:        $MAX_WAVES"
log "Tracks per wave:  $TRACKS_PER_WAVE"
log "Codex command:    $CODEX_CMD"
log "═══════════════════════════════════════════════"

if [[ "$DRY_RUN" == "true" && "$MAX_WAVES" -gt 1 ]]; then
  log "Dry run mode detected. Limiting preview to a single wave."
  MAX_WAVES=1
fi

for ((wave=1; wave<=MAX_WAVES; wave++)); do
  log ""
  log "──────── WAVE $wave of $MAX_WAVES ────────"

  # Step 1: Get current state
  log "Running resume script..."
  resume_json=$(get_resume_state)

  if [[ -z "$resume_json" ]] || ! echo "$resume_json" | python3 -c "import json,sys; json.load(sys.stdin)" &>/dev/null; then
    log "ERROR: resume script returned invalid JSON"
    log "Output: $resume_json"
    exit 2
  fi

  # Parse resume state
  next_action=$(echo "$resume_json" | python3 -c "import json,sys; print(json.load(sys.stdin).get('next_action','unknown'))")
  total=$(echo "$resume_json" | python3 -c "import json,sys; print(json.load(sys.stdin).get('total',0))")
  verified=$(echo "$resume_json" | python3 -c "import json,sys; print(json.load(sys.stdin).get('verified',0))")
  message=$(echo "$resume_json" | python3 -c "import json,sys; print(json.load(sys.stdin).get('message',''))")

  log "State: action=$next_action verified=$verified/$total"
  log "Message: $message"

  # Step 2: Check if done
  if [[ "$next_action" == "complete" ]]; then
    log "Resume script says complete. Running gate to confirm..."
    if run_gate; then
      log ""
      log "═══════════════════════════════════════════════"
      log "✅ SUPERCONDUCTOR COMPLETE"
      log "All $total requirements verified in $wave wave(s)."
      log "═══════════════════════════════════════════════"
      exit 0
    else
      log "Gate failed despite resume saying complete. Continuing..."
    fi
  fi

  # Step 3: Handle non-worker actions
  if [[ "$next_action" == "start_fresh" ]]; then
    log "ERROR: No superconductor run found. Use --setup to initialize."
    exit 2
  fi

  if [[ "$next_action" == "decompose" ]]; then
    log "Requirements still pending decomposition. Running Stage 6..."
    invoke_codex "Run /conductor:superconductor Stage 6: decompose all pending requirements into domain tracks. Then run Stage 7 to generate track directories. Do NOT start implementation." "$wave"
    continue
  fi

  if echo "$next_action" | grep -q "resume_stage_"; then
    stage_num=$(echo "$next_action" | sed 's/resume_stage_//')
    log "Resuming investigation at Stage $stage_num..."
    invoke_codex "Run /conductor:superconductor resuming at Stage ${stage_num}. Complete Stages ${stage_num} through 7 (investigation, closure, sufficiency, decomposition, track generation). Do NOT start implementation (Stage 8)." "$wave"
    continue
  fi

  if [[ "$next_action" == "run_reviews" ]]; then
    log "Running reviews for implemented requirements..."
    invoke_codex "Run /conductor:review for all implemented-but-unverified requirements. After review, update requirements-matrix.json to mark reviewed requirements as 'verified' with evidence." "$wave"
    continue
  fi

  # Step 4: Fan out workers — the main loop body
  if [[ "$next_action" == "fan_out_workers" || "$next_action" == "investigate" ]]; then
    # Extract incomplete tracks
    incomplete_tracks=$(echo "$resume_json" | python3 -c "
import json, sys
data = json.load(sys.stdin)
tracks = data.get('incomplete_tracks', [])
# Take the requested batch size
batch = tracks[:${TRACKS_PER_WAVE}]
print(json.dumps(batch))
")

    if [[ "$incomplete_tracks" == "[]" || -z "$incomplete_tracks" ]]; then
      log "No incomplete tracks found but gate hasn't passed. Checking matrix..."
      # Force a gate run to get accurate status
      if run_gate; then
        log "Gate passed!"
        exit 0
      fi
      log "Gate failed but no tracks to work on. Possible matrix/plan mismatch."
      log "Running recovery: asking codex to reconcile matrix with track state..."
      invoke_codex "The superconductor requirements-matrix.json shows incomplete requirements but no incomplete tracks were found. Read the matrix and all track plan.md files. For any requirement marked 'in-track' or 'implemented' whose track plan shows all tasks [x], update the requirement status to 'verified' with evidence. Commit the updated matrix." "$wave"
      continue
    fi

    # Build focused prompt
    prompt=$(build_worker_prompt "$incomplete_tracks" "$wave" "$total" "$verified")

    if [[ -z "$prompt" ]]; then
      log "ERROR: Failed to build worker prompt"
      exit 2
    fi

    # Invoke codex
    invoke_codex "$prompt" "$wave"

    # Step 5: Run the gate
    log "Wave $wave complete. Running completion gate..."
    if run_gate; then
      log ""
      log "═══════════════════════════════════════════════"
      log "✅ SUPERCONDUCTOR COMPLETE"
      log "All $total requirements verified in $wave wave(s)."
      log "═══════════════════════════════════════════════"
      exit 0
    fi

    log "Gate failed. Continuing to next wave..."
  fi
done

# If we get here, max waves exhausted
log ""
log "═══════════════════════════════════════════════"
log "⚠️  MAX WAVES REACHED ($MAX_WAVES)"
log "Run the driver again to continue, or check"
log "the matrix for stuck requirements."
log "═══════════════════════════════════════════════"
run_gate || true
exit 1
