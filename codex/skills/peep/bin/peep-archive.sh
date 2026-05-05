#!/usr/bin/env bash
set -euo pipefail

tmp_dir=""

fail() {
  local message="$*"
  if [[ -n "${tmp_dir:-}" && -d "$tmp_dir" ]]; then
    rm -rf -- "$tmp_dir"
  fi
  printf 'peep-archive: FAIL: %s\n' "$message" >&2
  exit 1
}

usage() {
  cat >&2 <<'USAGE'
Usage: peep-archive.sh \
  --spec-file <path> \
  --contract-file <path> \
  --brief-file <path> \
  --image-file <path> \
  --summary <one line>
USAGE
  exit 1
}

spec_file=""
contract_file=""
brief_file=""
image_file=""
summary=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --spec-file)
      [[ $# -ge 2 ]] || fail "--spec-file requires a path"
      spec_file="$2"
      shift 2
      ;;
    --contract-file)
      [[ $# -ge 2 ]] || fail "--contract-file requires a path"
      contract_file="$2"
      shift 2
      ;;
    --brief-file)
      [[ $# -ge 2 ]] || fail "--brief-file requires a path"
      brief_file="$2"
      shift 2
      ;;
    --image-file)
      [[ $# -ge 2 ]] || fail "--image-file requires a path"
      image_file="$2"
      shift 2
      ;;
    --summary)
      [[ $# -ge 2 ]] || fail "--summary requires a value"
      summary="$2"
      shift 2
      ;;
    -h|--help)
      usage
      ;;
    *)
      fail "unknown argument: $1"
      ;;
  esac
done

[[ -n "$spec_file" && -n "$contract_file" && -n "$brief_file" && -n "$image_file" && -n "$summary" ]] || usage
[[ "$summary" != *$'\n'* ]] || fail "summary must be one line"

for pair in \
  "spec-file:$spec_file" \
  "contract-file:$contract_file" \
  "brief-file:$brief_file"; do
  label=${pair%%:*}
  path=${pair#*:}
  [[ -f "$path" ]] || fail "$label does not exist: $path"
  [[ -s "$path" ]] || fail "$label is empty: $path"
done

[[ -f "$image_file" ]] || fail "image-file does not exist: $image_file"

image_bytes=$(wc -c < "$image_file" | tr -d '[:space:]')
[[ "$image_bytes" =~ ^[0-9]+$ ]] || fail "could not determine image-file size: $image_file"
image_file_report=$(file -b -- "$image_file")
if [[ "$image_file_report" != *"PNG image"* || "$image_bytes" -lt 1024 ]]; then
  fail "not a valid PNG: path=$image_file bytes=$image_bytes file=$image_file_report"
fi

if ! grep -Eq '^UI_BEHAVIOR_AFFECTING:[[:space:]]*(yes|no)[[:space:]]*$' "$contract_file"; then
  fail "contract missing UI_BEHAVIOR_AFFECTING; v2.3 templates require a line matching ^UI_BEHAVIOR_AFFECTING:\\s*(yes|no)\\s*$"
fi

repo_root="/home/david/david-harness"
archive_root="/home/david/peep-archive"

ensure_archive_worktree() {
  if [[ -d "$archive_root" ]]; then
    return 0
  fi

  cd "$repo_root"
  if ! git show-ref --verify --quiet refs/heads/peep; then
    git fetch origin peep:peep 2>/dev/null || {
      local bootstrap_dir
      bootstrap_dir=$(mktemp -d /tmp/peep-bootstrap.XXXXXX)
      git worktree add --detach "$bootstrap_dir" >/dev/null
      (
        cd "$bootstrap_dir"
        git checkout --orphan peep >/dev/null
        git rm -rf . >/dev/null 2>&1 || true
        printf '# peep archive\n\nOrphan branch storing peep contracts and checkit verification runs.\n' > README.md
        git add README.md
        git -c user.email=david@kijko.nl -c user.name=david commit -m "init orphan branch peep" >/dev/null
      )
      git worktree remove "$bootstrap_dir" >/dev/null
      git push -u origin peep >/dev/null
    }
  fi
  git worktree add "$archive_root" peep >/dev/null
}

ensure_archive_worktree
[[ -d "$archive_root/.git" || -f "$archive_root/.git" ]] || fail "archive worktree is not a git worktree: $archive_root"

sha_full=$(sha256sum -- "$spec_file" | awk '{print $1}')
peep_id="peep-${sha_full:0:8}"
archive="$archive_root/$peep_id"

if [[ -f "$archive/spec.txt" ]]; then
  if ! diff -q -- "$spec_file" "$archive/spec.txt" >/dev/null; then
    peep_id="peep-${sha_full:0:12}"
    archive="$archive_root/$peep_id"
    if [[ -f "$archive/spec.txt" ]] && ! diff -q -- "$spec_file" "$archive/spec.txt" >/dev/null; then
      fail "sha12 collision at $peep_id"
    fi
  fi
fi

tmp_dir="$archive_root/${peep_id}.tmp.$$"
rm -rf -- "$tmp_dir"
mkdir -p -- "$tmp_dir"
cp -- "$spec_file" "$tmp_dir/spec.txt"
cp -- "$contract_file" "$tmp_dir/contract.md"
cp -- "$brief_file" "$tmp_dir/mental-model.brief.md"
cp -- "$image_file" "$tmp_dir/mental-model.png"

rm -rf -- "$archive"
mv -- "$tmp_dir" "$archive"
tmp_dir=""

cd "$archive_root"
git add -- "$peep_id/"
if ! git diff --cached --quiet -- "$peep_id/"; then
  git -c user.email=david@kijko.nl -c user.name=david commit -m "$peep_id: $summary" >/dev/null
fi

push_ok=0
push_log=$(mktemp /tmp/peep-archive-push.XXXXXX.log)
for i in 1 2 3; do
  if git pull --rebase origin peep >"$push_log" 2>&1 && git push origin peep >>"$push_log" 2>&1; then
    push_ok=1
    break
  fi
  sleep 2
done

if [[ "$push_ok" -ne 1 ]]; then
  push_tail=$(tail -40 "$push_log" || true)
  rm -f -- "$push_log"
  fail "git pull --rebase/push failed after 3 attempts; tail: $push_tail"
fi
rm -f -- "$push_log"

printf 'peep-archive: ok peepID=%s path=%s\n' "$peep_id" "$archive"
