#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/devuser/macos-intent"
CTL="$ROOT/scripts/macos-intent"

usage() {
  cat <<USAGE
macbox-cli.sh <command>

Commands:
  status          Show docker/noVNC status
  creds           Print env creds
  logs            Tail container logs
  up              Start stack
  restart         Restart stack
  down            Stop stack
  endpoints       Show remote endpoints
  lan-on          Enable LAN binds
  lan-off         Disable LAN binds
  lock-ip <ip>    Allow only one remote IPv4 for VNC/noVNC
  unlock-ip       Remove lock-ip firewall rule
  set-pass <pass> Set NOVNC_PASS and restart
  vm-git-install  Install Git in macOS VM via control CLI
USAGE
}

require_root_dir() {
  [[ -d "$ROOT" ]] || { echo "Missing $ROOT" >&2; exit 1; }
  [[ -x "$CTL" ]] || { echo "Missing control CLI: $CTL" >&2; exit 1; }
}

send() { "$CTL" type "$*" >/dev/null; "$CTL" sendkeys ret >/dev/null; }

cmd="${1:-}"
case "$cmd" in
  status) require_root_dir; "$CTL" status ;;
  creds) require_root_dir; "$CTL" creds ;;
  logs) docker logs --tail 100 macos-intent ;;
  up) require_root_dir; "$CTL" start ;;
  restart) require_root_dir; "$CTL" restart ;;
  down) require_root_dir; "$CTL" stop ;;
  endpoints) require_root_dir; "$CTL" endpoints ;;
  lan-on) require_root_dir; "$CTL" lan-on ;;
  lan-off) require_root_dir; "$CTL" lan-off ;;
  lock-ip) require_root_dir; shift; "$CTL" lock-ip "$@" ;;
  unlock-ip) require_root_dir; "$CTL" unlock-ip ;;
  set-pass) require_root_dir; shift; "$CTL" set-pass "$@" ;;
  vm-git-install)
    require_root_dir
    "$CTL" sendkeys ctrl-c >/dev/null || true
    "$CTL" sendkeys esc >/dev/null || true
    send clear
    send 'git --version'
    send 'touch /tmp/.com.apple.dt.CommandLineTools.installondemand.in-progress'
    send 'softwareupdate -l | grep -B 1 -E "Command Line Tools"'
    send 'PROD=$(softwareupdate -l 2>/dev/null | awk -F"*" "/Command Line Tools/{print \$2}" | sed "s/^ *Label: //;s/^ *//" | head -n1); echo "CLT=$PROD"'
    send 'if [ -n "$PROD" ]; then sudo softwareupdate -i "$PROD" --verbose; fi'
    send 'rm -f /tmp/.com.apple.dt.CommandLineTools.installondemand.in-progress'
    send 'xcode-select -p || sudo xcode-select --switch /Library/Developer/CommandLineTools'
    send 'if command -v brew >/dev/null 2>&1; then brew install git; fi'
    send 'git --version'
    echo "Sent robust VM Git install sequence (CLT/softwareupdate + brew fallback + git --version)."
    ;;
  *) usage; exit 1 ;;
esac
