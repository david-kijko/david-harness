# Source Routing & Deselection

When querying forensic-ingested notebooks with many sources (50+), **always** scope queries to relevant sources to reduce noise and improve answer quality.

## Why Source Routing Matters

NotebookLM queries all sources by default. A 120-source notebook floods the model with irrelevant context. Source routing:
- Reduces token waste (often 10x fewer chars sent to Gemini)
- Improves answer precision by excluding noise
- Speeds up queries

## How to Route

### Via MCP (`notebook_query` or `notebook_query_alias`)

Use `source_title_filters` to **include** only relevant sources:

```
notebook_query_alias(
  alias="@nlm_honcho",
  query="How does the deriver pipeline work?",
  source_title_filters=["src-deriver-"]
)
```

Multiple filters act as OR:

```
notebook_query_alias(
  alias="@nlm_honcho",
  query="How do SDKs wrap the API?",
  source_title_filters=["sdks-python-", "sdks-typescript-"]
)
```

### Via CLI (`nlm notebook query`)

```bash
NLM=/home/david/.local/bin/nlm
$NLM notebook query honcho "How does auth work?" --source-ids <id1>,<id2>
```

### Via `source_ids` (precise)

Use exact source IDs from the registry JSON:

```python
import json
reg = json.load(open("/tmp/forensic-ingest/honcho-registry.json"))
# Get specific source IDs
ids = [v["source_id"] for k, v in reg["sources"].items() if k.startswith("src-deriver")]
```

## Routing Decision Process

1. **Read the CODE-MAP-INDEX source first** — it contains a routing table mapping query topics to source groups
2. **Identify the area** — match the user's question to a source group (e.g., "SDK" → `sdks-*`, "database" → `migrations-*`)
3. **Include related deps** — if the question involves how X works, also include X's dependencies
4. **Deselect the rest** — exclude all source groups not relevant to the question
5. **For architecture questions** — include all sources (no deselection)

## Source Group Patterns for @nlm_honcho

| Group | Title Filter | What's In It |
|---|---|---|
| Server core | `src-utils-`, `src-deriver-`, `src-dreamer-` | Python backend: CRUD, dialectic, reasoning |
| HyperVisa | `src-hypervisa-` | Visualization renderer, MCP trinity |
| Telemetry | `src-telemetry` | Metrics, event emitter |
| Server infra | `server-` | Architecture, auth, routes, runtime |
| App layer | `app-` | Models, protocols, repositories, routes, services |
| Python SDK | `sdks-python-` | Python client library |
| TypeScript SDK | `sdks-typescript-` | TypeScript client library |
| MCP tools | `mcp-src-tools`, `packages-mcp` | MCP tool definitions |
| Agent pipeline | `apps-agent-` | Docs pipeline, KG builder, orchestrator |
| Packages | `packages-` | Harmony, iOS, playground, recorder, shared, web-integration |
| Client UI | `client-src-` | React components, pages |
| Web frontend | `apps-web-` | Docs site, wiki components |
| Docs (v1-v3) | `misc-isolates-` (7-19) | User documentation |
| Examples | `misc-isolates-` (21-23) | Integration examples |
| Config/skills | `misc-isolates-` (1-6, 24) | Claude skills, SVGs, READMEs |
| Migrations | `alembic`, `migrations-` | Database schema changes |
| Tests | `tests-` | E2E, integration tests |
| CI/CD | `-github` | GitHub workflows |
| Infra | `docker`, `root` | Dockerfile, root config |

## Anti-Patterns

- **Don't query all 120 sources** for a specific subsystem question
- **Don't exclude the CODE-MAP-INDEX** — it helps NLM understand the overall structure
- **Don't include tests** unless the question is about test coverage or test behavior
- **Don't include migrations** unless the question is about database schema
