#!/usr/bin/env bash
set -euo pipefail

model="${HEPHAESTUS_MODEL:-gpt-5.5}"
reasoning_effort="${HEPHAESTUS_REASONING_EFFORT:-high}"
sandbox="dangerous"
workdir="$PWD"
prompt_file=""
use_stdin=0

usage() {
  cat <<'EOF'
hephaestus [PROMPT]
hephaestus --file <brief.md> [--dir <path>] [--full-auto|--dangerous]
hephaestus -   # read prompt from stdin

Options:
  --file <path>           Read prompt from file
  --dir <path>            Working directory for codex exec
  --full-auto             Use workspace-write sandbox
  --dangerous             Use danger-full-access sandbox
  --reasoning-effort <v>  Override model reasoning effort
  -h, --help              Show help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --file)
      prompt_file="${2:?missing value for --file}"
      shift 2
      ;;
    --dir)
      workdir="${2:?missing value for --dir}"
      shift 2
      ;;
    --full-auto)
      sandbox="workspace-write"
      shift
      ;;
    --dangerous)
      sandbox="dangerous"
      shift
      ;;
    --reasoning-effort)
      reasoning_effort="${2:?missing value for --reasoning-effort}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -)
      use_stdin=1
      shift
      ;;
    --)
      shift
      break
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      break
      ;;
  esac
done

mkdir -p "$HOME/.hephaestus/outputs"

timestamp="$(date +%Y%m%d-%H%M%S)-$$"
output_file="$HOME/.hephaestus/outputs/hephaestus-$timestamp.md"
guard_prompt_file="$HOME/.hephaestus/outputs/hephaestus-$timestamp.prompt.txt"

codex_cmd=(
  codex exec
  -m "$model"
  -c "model_reasoning_effort=\"$reasoning_effort\""
  -c "model_instructions_file=\"$HOME/.codex/AGENTS.md\""
  -c "features.use_linux_sandbox_bwrap=false"
  --dangerously-bypass-approvals-and-sandbox
  -C "$workdir"
  -o "$output_file"
)

echo "[Hephaestus] Model: $model | Reasoning: $reasoning_effort | Sandbox: $sandbox | Dir: $workdir"
echo "[Hephaestus] Output: $output_file"

if [[ -n "$prompt_file" ]]; then
  echo "[Hephaestus] Task: $(head -n 1 "$prompt_file" 2>/dev/null || echo "...")"
  cp "$prompt_file" "$guard_prompt_file"
  cat "$prompt_file" | "${codex_cmd[@]}" -
elif [[ "$use_stdin" -eq 1 ]]; then
  echo "[Hephaestus] Task: stdin"
  cat > "$guard_prompt_file"
  "${codex_cmd[@]}" - < "$guard_prompt_file"
elif [[ $# -gt 0 ]]; then
  echo "[Hephaestus] Task: $1"
  printf '%s\n' "$*" > "$guard_prompt_file"
  "${codex_cmd[@]}" "$*"
else
  echo "No prompt provided." >&2
  usage >&2
  exit 2
fi

echo "[Hephaestus] Running completion_guard on $output_file"
if ! "$HOME/.local/bin/completion_guard" --file "$output_file" --prompt-file "$guard_prompt_file"; then
  echo "[Hephaestus] COMPLETION_GUARD rejected output. Hephaestus must be re-run with behavioral proof." >&2
  exit 2
fi
