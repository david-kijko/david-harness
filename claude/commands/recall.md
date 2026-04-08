Search persistent episodic memory for information across all past coding sessions (Claude Code, Codex, Hermes) and the current live session.

Run: `kijko-memory --limit 5 recall $ARGUMENTS`

This performs hybrid retrieval (BM25 + dense vector via nomic-embed-text) across 4 memory layers plus the live session, fuses results with RRF, then synthesizes an answer using GPT-5.4 with semi-formal reasoning and source citations.

Use this when:
- The user references something from a past session ("do you remember when...")
- You need context about previous work before proceeding
- Cross-referencing decisions or outcomes across sessions
- Before asking the user to repeat information they've shared before

Report the findings including citations. If GAPS are identified in the response, relay them honestly.
