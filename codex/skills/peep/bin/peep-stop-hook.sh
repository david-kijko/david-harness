#!/usr/bin/env bash
set -euo pipefail

input=$(cat)

json_value() {
  local expr="$1"
  python3 -c 'import json, sys
expr = sys.argv[1]
try:
    data = json.load(sys.stdin)
except Exception:
    print("")
    raise SystemExit(0)
cur = data
for part in expr.split("."):
    if not part:
        continue
    if isinstance(cur, dict) and part in cur:
        cur = cur[part]
    else:
        print("")
        raise SystemExit(0)
if cur is None:
    print("")
elif isinstance(cur, (dict, list)):
    print(json.dumps(cur))
else:
    print(str(cur))' "$expr" <<< "$input"
}

expand_path() {
  local path="$1"
  if [[ "$path" == ~/* ]]; then
    printf '%s/%s\n' "$HOME" "${path#~/}"
  else
    printf '%s\n' "$path"
  fi
}

transcript_path=$(json_value transcript_path)
transcript_path=$(expand_path "$transcript_path")

if [[ -z "$transcript_path" || ! -f "$transcript_path" ]]; then
  exit 0
fi

claim_pattern='peep contract|filled the certificate|READY TO IMPLEMENT|peep-[0-9a-f]{8}|peep self-archive|mental-model\.png|SELF-ARCHIVE'
claim_matches=$(grep -E -i -m 3 -- "$claim_pattern" "$transcript_path" || true)
if [[ -z "$claim_matches" ]]; then
  exit 0
fi

session_start=$(python3 -c 'import json, sys
from datetime import datetime, timezone
raw=sys.stdin.read()
try:
    data=json.loads(raw)
except Exception:
    data={}
keys=["session_start_time","session_start_timestamp","sessionStartTime","start_time","started_at","startedAt","created_at"]
for key in keys:
    value=data.get(key)
    if value:
        print(value)
        raise SystemExit(0)
print("")' <<< "$input")

if [[ -z "$session_start" ]]; then
  session_start=$(python3 -c 'import json, sys
path=sys.argv[1]
keys=("timestamp","created_at","createdAt","time")
try:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                obj=json.loads(line)
            except Exception:
                continue
            for key in keys:
                value=obj.get(key)
                if value:
                    print(value)
                    raise SystemExit(0)
except Exception:
    pass
print("")' "$transcript_path")
fi

if [[ -z "$session_start" ]]; then
  session_start="12 hours ago"
fi

archive_root="/home/david/peep-archive"
fresh_archives=""
if [[ -d "$archive_root" ]]; then
  fresh_archives=$(git -C "$archive_root" log --since="$session_start" --name-only --pretty=format: -- 'peep-*/spec.txt' 2>/dev/null | grep -E '^peep-[0-9a-f]{8,12}/spec\.txt$' || true)
fi

if [[ -n "$fresh_archives" ]]; then
  exit 0
fi

{
  printf 'peep-stop-hook: BLOCK: this session contains peep contract claims but no\n'
  printf 'archive folder was produced this session via peep-archive.sh. Either:\n'
  printf '  a) Run peep-archive.sh to actually produce the artifact, OR\n'
  printf '  b) Retract the claim — peep is not complete without the archive.\n'
  printf 'Detected claims:\n'
  printf '%s\n' "$claim_matches" | sed -e 's/^/  /'
} >&2
exit 2
