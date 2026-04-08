Search episodic memory and return raw session excerpts ranked by relevance.

Run: `kijko-memory --limit 5 verbatim $ARGUMENTS`

Returns actual session transcripts — tool calls, messages, commands, diffs — from past sessions including the current live session. Results include provenance citations (session:seq_start-seq_end).

Use when the user wants to see exactly what happened — raw evidence, not a summary.

Filters:
- `--agent codex` or `--agent claude_code` to narrow by agent
- `--limit N` to control result count
