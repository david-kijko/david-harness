# Session Verification

Use the session artifact, not terminal scrollback, as the main proof source.

## Why

- the remote TUI emits control sequences and update prompts
- answers can be visible in the PTY but hard to parse reliably
- Codex writes a clean JSONL session record under `~/.codex/sessions/`

## Find The Latest Session

```bash
ssh -i /home/david/.ssh/kijko_deploy_key -o BatchMode=yes root@157.90.215.60 \
  'find /home/david/.codex/sessions -type f | sort | tail -n 5'
```

## Inspect The Latest File

```bash
ssh -i /home/david/.ssh/kijko_deploy_key -o BatchMode=yes root@157.90.215.60 \
  'latest=$(find /home/david/.codex/sessions -type f | sort | tail -n 1); \
   echo FILE:$latest; \
   grep -nE "DISCOVERED|NOT DISCOVERED|skill|SKILL|invalid YAML|launch-app-server-agents" "$latest" | sed -n "1,200p"'
```

## What To Look For

- `DISCOVERED` or the exact final answer you requested
- calls or reads against the skill path you expected
- absence of `invalid YAML` or other skill-loading errors

## Common Failures

### Invalid YAML in `SKILL.md`

Symptom:

- Codex skips the skill
- app-server log or session shows `invalid YAML`

Fix:

- keep frontmatter to `name` and `description`
- use valid YAML block style for long descriptions
- reinstall the skill and rerun a fresh session

### Permission errors reading files

Symptom:

- session tries to `sed` a file and gets permission denied under sandbox

Meaning:

- the session still discovered the skill from the registry, but it could not read the file body through the tool

Verify through:

- skill name appearing in the session registry
- final answer acknowledging the requested skill

### Update prompt noise

Symptom:

- session opens with a Codex upgrade banner before the actual task

Handling:

- skip the update for the test session
- continue to the actual prompt
- verify through the session JSONL instead of the terminal
