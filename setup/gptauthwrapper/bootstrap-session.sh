#!/usr/bin/env bash
# Bootstrap GPTAuthWrapper with its own independent OAuth session.
#
# Watches ~/.codex/auth.json for a fresh write (from Codex CLI/extension),
# then immediately uses the new refresh_token to perform our OWN refresh,
# forking the session. After this, GPTAuthWrapper has an independent token
# chain that never conflicts with Codex.
#
# This is a ONE-TIME operation. Run it, then trigger any Codex CLI command
# (e.g. `codex login --device-auth` or just use Codex normally).

set -euo pipefail

CODEX_AUTH="/home/david/.codex/auth.json"
WRAPPER_AUTH="/home/david/.gptauthwrapper/auth.json"
OAUTH_CLIENT_ID="app_EMoamEEZ73f0CkXaXp7hrann"
OAUTH_ISSUER="https://auth.openai.com"

mkdir -p "$(dirname "$WRAPPER_AUTH")"

echo "=== GPTAuthWrapper Session Bootstrap ==="
echo ""
echo "Watching $CODEX_AUTH for a fresh token write..."
echo "Trigger a refresh by running any Codex command, or: codex login --device-auth"
echo ""

# Record current state
BEFORE_MTIME=$(stat -c '%Y' "$CODEX_AUTH" 2>/dev/null || echo 0)

# Watch for file change
while true; do
  inotifywait -q -e modify -e create "$CODEX_AUTH" 2>/dev/null || {
    # Fallback: poll if inotifywait not available
    sleep 2
    CURRENT_MTIME=$(stat -c '%Y' "$CODEX_AUTH" 2>/dev/null || echo 0)
    [ "$CURRENT_MTIME" = "$BEFORE_MTIME" ] && continue
  }

  echo "Detected fresh auth.json write. Forking session..."

  # Extract the fresh refresh token
  REFRESH_TOKEN=$(python3 -c "import json; print(json.load(open('$CODEX_AUTH'))['tokens']['refresh_token'])")

  # Use it immediately to get our OWN tokens (this consumes the token,
  # but Codex already got its own new one from the same refresh response)
  RESPONSE=$(curl -sf --max-time 10 "${OAUTH_ISSUER}/oauth/token" \
    -H "content-type: application/x-www-form-urlencoded" \
    -d "grant_type=refresh_token&refresh_token=${REFRESH_TOKEN}&client_id=${OAUTH_CLIENT_ID}") || {
    echo "Refresh failed — token may already be consumed. Waiting for next write..."
    BEFORE_MTIME=$(stat -c '%Y' "$CODEX_AUTH" 2>/dev/null || echo 0)
    continue
  }

  # Build our own auth.json
  python3 -c "
import json, sys
resp = json.loads('''$RESPONSE''')
auth = {
  'auth_mode': 'chatgpt',
  'tokens': {
    'id_token': resp.get('id_token'),
    'access_token': resp['access_token'],
    'refresh_token': resp['refresh_token'],
    'account_id': None
  },
  'last_refresh': __import__('datetime').datetime.utcnow().isoformat() + 'Z'
}
# Extract account_id from JWT
import base64
for tok in [resp.get('id_token',''), resp.get('access_token','')]:
  if not tok: continue
  try:
    claims = json.loads(base64.urlsafe_b64decode(tok.split('.')[1] + '=='))
    aid = claims.get('chatgpt_account_id') or (claims.get('https://api.openai.com/auth') or {}).get('chatgpt_account_id')
    if aid:
      auth['tokens']['account_id'] = aid
      break
  except: pass
with open('$WRAPPER_AUTH', 'w') as f:
  json.dump(auth, f, indent=2)
import os; os.chmod('$WRAPPER_AUTH', 0o600)
print('account_id:', auth['tokens']['account_id'])
"

  echo ""
  echo "Session forked successfully to: $WRAPPER_AUTH"
  echo "GPTAuthWrapper now has an independent token chain."
  echo ""
  echo "Restart the service to pick it up:"
  echo "  sudo systemctl restart gptauthwrapper"
  exit 0
done
