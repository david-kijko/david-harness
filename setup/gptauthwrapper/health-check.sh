#!/usr/bin/env bash
# GPTAuthWrapper health check — designed for cron or systemd timer.
# Returns 0 if healthy, 1 if degraded, 2 if down.
# Sends a desktop notification + logs to journal on failure.
set -euo pipefail

HEALTH_URL="${GPTAUTHWRAPPER_HEALTH_URL:-http://127.0.0.1:4141/health}"
NOTIFY_CMD="${GPTAUTHWRAPPER_NOTIFY_CMD:-notify-send}"
LOG_TAG="gptauthwrapper-healthcheck"

response=$(curl -sf --max-time 5 "$HEALTH_URL" 2>/dev/null) || {
  msg="GPTAuthWrapper is DOWN — /health unreachable at $HEALTH_URL"
  logger -t "$LOG_TAG" -p user.crit "$msg"
  $NOTIFY_CMD -u critical "GPTAuthWrapper DOWN" "$msg" 2>/dev/null || true
  echo "$msg" >&2
  exit 2
}

ok=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('ok', False))" 2>/dev/null)
token_status=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('auth',{}).get('token_status','unknown'))" 2>/dev/null)
last_error=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('auth',{}).get('last_error','') or '')" 2>/dev/null)

if [ "$ok" = "True" ]; then
  echo "OK: GPTAuthWrapper healthy (token=$token_status)"
  exit 0
fi

msg="GPTAuthWrapper DEGRADED — token=$token_status"
[ -n "$last_error" ] && msg="$msg error=$last_error"

if [ "$token_status" = "expired" ] || [ "$token_status" = "missing" ]; then
  msg="$msg — Run 'codex login' to re-authenticate"
  logger -t "$LOG_TAG" -p user.crit "$msg"
  $NOTIFY_CMD -u critical "GPTAuthWrapper AUTH EXPIRED" "$msg" 2>/dev/null || true
else
  logger -t "$LOG_TAG" -p user.warning "$msg"
  $NOTIFY_CMD -u normal "GPTAuthWrapper Degraded" "$msg" 2>/dev/null || true
fi

echo "$msg" >&2
exit 1
