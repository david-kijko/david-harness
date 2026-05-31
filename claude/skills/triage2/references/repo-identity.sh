#!/usr/bin/env bash
# Deterministic, worktree-safe repo identity for triage Gotcha filing.
#
# The whole point: a linked worktree's `rev-parse --show-toplevel` returns the
# WORKTREE path, which would mint a phantom repo identity. We key off the COMMON
# git dir (shared by all worktrees) + the origin remote, so every worktree of a
# repo resolves to the SAME canonical key, root, and Gotchas.md path.
#
# Usage:
#   source /home/david/.claude/skills/triage2/references/repo-identity.sh
#   eval "$(triage_repo_identity /path/inside/repo-or-worktree)"
#   echo "$TRIAGE_REPO_KEY $TRIAGE_REPO_ROOT $TRIAGE_GOTCHAS"
#
# Emits shell-eval'able assignments (or TRIAGE_ERR on failure).

triage_repo_identity() {
  local p="${1:-.}"
  if ! git -C "$p" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    printf "TRIAGE_ERR=%q\n" "not a git work tree: $p"; return 1
  fi
  local commondir root remote key slug
  # COMMON git dir is shared across all linked worktrees -> dirname = MAIN root.
  commondir="$(git -C "$p" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)"
  root="$(cd "$(dirname "$commondir")" && pwd)"
  remote="$(git -C "$p" config --get remote.origin.url 2>/dev/null)"
  if [ -n "$remote" ]; then
    # Normalize https/ssh/scp forms to host/owner/repo (no scheme, user, or .git).
    key="$(printf '%s' "$remote" \
      | sed -E 's#^[a-zA-Z][a-zA-Z0-9+.-]*://##; s#^[^@/]+@##; s#:#/#; s#\.git$##; s#/+$##')"
  else
    key="$root"                       # no remote -> canonical absolute path is the key
  fi
  slug="$(printf '%s' "$key" | sed -E 's#[/:]+#__#g; s#[^A-Za-z0-9_.-]#_#g')"
  printf "TRIAGE_REPO_KEY=%q\n"  "$key"
  printf "TRIAGE_REPO_ROOT=%q\n" "$root"
  printf "TRIAGE_GOTCHAS=%q\n"   "$root/Gotchas.md"
  printf "TRIAGE_REPO_SLUG=%q\n" "$slug"
  printf "TRIAGE_REMOTE=%q\n"    "$remote"
}

# Assert the repo at $1 has the expected key $2; non-zero exit + message on mismatch.
# Use this BEFORE writing a Gotcha so an entry can never land in the wrong repo.
triage_assert_repo() {
  local p="$1" expect="$2" out
  out="$(triage_repo_identity "$p")" || { echo "$out" >&2; return 2; }
  eval "$out"
  if [ "$TRIAGE_REPO_KEY" != "$expect" ]; then
    echo "TRIAGE MISFILE GUARD: $p resolves to '$TRIAGE_REPO_KEY' but expected '$expect' — refusing to write." >&2
    return 1
  fi
  printf '%s\n' "$out"
}

# Allow direct invocation: `repo-identity.sh <path>` prints the identity block.
if [ "${BASH_SOURCE[0]}" = "$0" ]; then triage_repo_identity "${1:-.}"; fi
