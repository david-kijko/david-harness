#!/usr/bin/env bash
set -euo pipefail

# Install David Harness skills for OpenAI Codex CLI
# Symlinks all skills and copies config into ~/.codex/

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
CODEX_SKILLS_DIR="$CODEX_HOME/skills"
CODEX_AGENTS_DIR="$CODEX_HOME/agents"

echo "[david-harness] Installing Codex skills..."

# Create directories
mkdir -p "$CODEX_SKILLS_DIR"
mkdir -p "$CODEX_AGENTS_DIR"
mkdir -p "$HOME/.hephaestus/outputs"

# Symlink skills
for skill_dir in "$REPO_DIR/codex/skills"/*/; do
  skill_name="$(basename "$skill_dir")"
  target="$CODEX_SKILLS_DIR/$skill_name"

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

# Copy AGENTS.md (global Hephaestus identity)
if [ -f "$CODEX_HOME/AGENTS.md" ]; then
  echo "  Backing up existing AGENTS.md -> AGENTS.md.bak"
  cp "$CODEX_HOME/AGENTS.md" "$CODEX_HOME/AGENTS.md.bak"
fi
cp "$REPO_DIR/codex/AGENTS.md" "$CODEX_HOME/AGENTS.md"
echo "  Installed: AGENTS.md (global Hephaestus identity)"

# Copy agent configs
for agent_file in "$REPO_DIR/codex/agents"/*; do
  agent_name="$(basename "$agent_file")"
  target="$CODEX_AGENTS_DIR/$agent_name"

  if [ -f "$target" ]; then
    echo "  Updating agent: $agent_name"
  else
    echo "  Installing agent: $agent_name"
  fi

  cp "$agent_file" "$target"
done

# Install Hephaestus CLI
echo ""
echo "  Installing Hephaestus CLI..."
if command -v hephaestus &>/dev/null; then
  echo "  hephaestus CLI already installed at: $(command -v hephaestus)"
else
  if [ -w /usr/local/bin ]; then
    cp "$REPO_DIR/hephaestus/run.sh" /usr/local/bin/hephaestus
    chmod +x /usr/local/bin/hephaestus
    echo "  Installed: /usr/local/bin/hephaestus"
  else
    echo "  Cannot write to /usr/local/bin/. Run with sudo:"
    echo "    sudo cp $REPO_DIR/hephaestus/run.sh /usr/local/bin/hephaestus"
    echo "    sudo chmod +x /usr/local/bin/hephaestus"
  fi
fi

echo ""
echo "[david-harness] Codex installation complete."
echo "  Skills: $(ls -d "$CODEX_SKILLS_DIR"/*/ 2>/dev/null | wc -l) installed"
echo "  Agents: $(ls "$CODEX_AGENTS_DIR"/* 2>/dev/null | wc -l) configured"
echo ""
echo "NOTE: You must configure ~/.codex/config.toml manually."
echo "See: hephaestus/INSTALL.md for config.toml template."
