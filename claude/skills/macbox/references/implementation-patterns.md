# Implementation Patterns (researched with Exa)

Primary source used:
- Anthropic official docs: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices

Patterns applied in this skill:
1. Keep `SKILL.md` concise and task-oriented.
2. Put detailed command recipes in `references/` (progressive disclosure).
3. Use precise trigger language in `description` so skill activation is reliable.
4. Include deterministic scripts in `scripts/` for repeatable operations.
5. Validate with `quick_validate.py` after any change.
