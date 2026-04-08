Store a curated fact in persistent episodic memory with trust scoring and provenance.

Run: `kijko-memory remember $ARGUMENTS`

This persists as an L3 assertion — a curated fact that is always included in future recall/verbatim search results. Facts start at trust=0.5 and can be adjusted with feedback.

Use for: infrastructure facts, project decisions, debugging outcomes, lessons learned, or anything that should be recalled in future sessions.

Additional fact management commands:
- `kijko-memory facts` — list all active assertions
- `kijko-memory facts <query>` — search assertions by keyword
- `kijko-memory forget <id>` — remove an assertion
- `kijko-memory feedback <id> +` — increase trust score
- `kijko-memory feedback <id> -` — decrease trust score
