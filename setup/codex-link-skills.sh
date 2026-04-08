#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: codex-link-skills [--force] [--verify] <bundle-skills-dir>

Links each immediate child skill directory that contains a SKILL.md file into
${CODEX_HOME:-$HOME/.codex}/skills.

Examples:
  codex-link-skills ~/.codex/superpowers/skills
  codex-link-skills --verify ~/.codex/superpowers/skills
  codex-link-skills --force ~/.codex/superpowers/skills
EOF
}

force=0
verify=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --force)
      force=1
      shift
      ;;
    --verify)
      verify=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
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

if [[ $# -ne 1 ]]; then
  usage >&2
  exit 2
fi

bundle_dir="$1"
if [[ ! -d "$bundle_dir" ]]; then
  echo "Bundle skills directory not found: $bundle_dir" >&2
  exit 1
fi

codex_home="${CODEX_HOME:-$HOME/.codex}"
skills_root="$codex_home/skills"
mkdir -p "$skills_root"

bundle_dir="$(realpath "$bundle_dir")"
skills_root="$(realpath "$skills_root")"

shopt -s nullglob

found=0
linked=0
unchanged=0
conflicts=0

for skill_dir in "$bundle_dir"/*; do
  [[ -d "$skill_dir" ]] || continue
  [[ -f "$skill_dir/SKILL.md" ]] || continue

  found=1
  name="$(basename "$skill_dir")"
  target="$skills_root/$name"

  if [[ -L "$target" ]]; then
    current_target="$(readlink -f "$target" || true)"
    if [[ "$current_target" == "$skill_dir" ]]; then
      echo "OK     $name"
      unchanged=$((unchanged + 1))
      continue
    fi
  fi

  if [[ -e "$target" || -L "$target" ]]; then
    if [[ "$force" -ne 1 ]]; then
      echo "ERROR  $name already exists at $target" >&2
      conflicts=$((conflicts + 1))
      continue
    fi
    rm -rf "$target"
  fi

  ln -s "$skill_dir" "$target"
  echo "LINK   $name -> $skill_dir"
  linked=$((linked + 1))
done

if [[ "$found" -ne 1 ]]; then
  echo "No child skill directories with SKILL.md were found in $bundle_dir" >&2
  exit 1
fi

echo
echo "Summary: linked=$linked unchanged=$unchanged conflicts=$conflicts"
echo "Skills root: $skills_root"
echo "Note: personal Codex skills live under \$CODEX_HOME/skills, not ~/.agents/skills."

if [[ "$verify" -eq 1 ]]; then
  tmp_output="$(mktemp)"
  codex exec --skip-git-repo-check --ephemeral -C "$HOME" -m gpt-5.4-mini -o "$tmp_output" \
    "List the available skills from your current session as a plain newline-separated list of exact skill names only." \
    >/dev/null 2>&1 || true

  echo
  echo "Fresh Codex session reports:"
  if [[ -s "$tmp_output" ]]; then
    sed -n '1,200p' "$tmp_output"
  else
    echo "(verification did not return skill output)"
  fi
  rm -f "$tmp_output"
fi

if [[ "$conflicts" -gt 0 ]]; then
  exit 1
fi
