#!/usr/bin/env bash
set -euo pipefail

# Install David Harness skills for Claude Code
# Symlinks all skills and commands into ~/.claude/

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
CLAUDE_SKILLS_DIR="$HOME/.claude/skills"
CLAUDE_COMMANDS_DIR="$HOME/.claude/commands"

echo "[david-harness] Installing Claude Code skills..."

# Create directories
mkdir -p "$CLAUDE_SKILLS_DIR"
mkdir -p "$CLAUDE_COMMANDS_DIR"

# Symlink skills
for skill_dir in "$REPO_DIR/claude/skills"/*/; do
  skill_name="$(basename "$skill_dir")"
  target="$CLAUDE_SKILLS_DIR/$skill_name"

  if [ -L "$target" ]; then
    echo "  Updating: $skill_name"
    rm "$target"
  elif [ -d "$target" ]; then
    echo "  Skipping (directory exists): $skill_name"
    continue
  else
    echo "  Installing: $skill_name"
  fi

  ln -s "$skill_dir" "$target"
done

# Copy commands (not symlinked since they're simple files)
for cmd_file in "$REPO_DIR/claude/commands"/*.md; do
  cmd_name="$(basename "$cmd_file")"
  target="$CLAUDE_COMMANDS_DIR/$cmd_name"

  if [ -f "$target" ]; then
    echo "  Updating command: $cmd_name"
  else
    echo "  Installing command: $cmd_name"
  fi

  cp "$cmd_file" "$target"
done

echo ""
echo "[david-harness] Claude Code installation complete."
echo "  Skills:   $(ls -d "$CLAUDE_SKILLS_DIR"/*/ 2>/dev/null | wc -l) installed"
echo "  Commands: $(ls "$CLAUDE_COMMANDS_DIR"/*.md 2>/dev/null | wc -l) installed"
echo ""
echo "Third-party plugins must be installed separately."
echo "See: claude/plugins/PLUGINS.md"
