SEMI-FORMAL GREENFIELD CONSTRUCTION CERTIFICATE

DEFINITIONS
D1: SUFFICIENT iff every Rn has at least one created file/test mapped to it.
D2: MINIMAL iff every created file, dependency, and concept discharges at least one Rn or contract.
D3: INTERNALLY COHERENT iff interfaces, runtime assumptions, and verification do not contradict one another.
D4: VERIFIABLE iff a runnable command exercises a user-visible path and every Rn has such coverage.

SPEC (verbatim from the user)
See the byte-exact spec.txt archived alongside this contract.

SPEC DECOMPOSITION
R1: Build a separate private david-kijko/homer-API repository and service; do not modify, import, restart, or share a listener/tunnel process with homer-mcp. — Non-goal: adding routes to homer-mcp.
R2: Serve at https://homer-api.kijko.nl through its own named Cloudflare tunnel to 127.0.0.1:8767, with its own generated ~/.homer-api/api-key.txt. — Non-goal: reusing the Homer MCP key or tunnel.
R3: Work as a normal Anthropic base URL with the current official SDK: caller sets base_url to the origin and api_key to the Homer API key; both X-Api-Key and Authorization: Bearer forms authenticate. — Non-goal: a custom client protocol.
R4: Cover the full current Anthropic HTTP control surface by forwarding every method/path/query/body under /v1, including stable, beta, Admin, Compliance, Files, Skills, Managed Agents, and Tunnels routes, without a local endpoint allow-list or schema translation. — Non-goal: fabricating entitlements absent from the OAuth account.
R5: Preserve multipart boundaries, large request streaming, status, request-id, duplicate end-to-end headers, native JSON errors, SSE event bytes/timing, JSONL and binary response bytes, and cancellation. Strip hop-by-hop and caller auth only; rebase upstream batch results_url/Location links that would bypass the configured base URL. — Non-goal: OpenAI compatibility.
R6: Use this machine's existing Claude OAuth for upstream authorization without exposing it. Homer API may read ~/.claude/.credentials.json, but Claude CLI remains its only writer/refresh owner. — Non-goal: copying credentials, implementing an independent refresh grant, or rotating the shared file directly.
R7: Establish tests, strict typing/lint/build/CI, service assets, operator docs, and a sanitized live verification command; prove local and public behavior with official anthropic==0.116.0. — Non-goal: claiming CI or product entitlements without literal runs.

OPEN ASSUMPTIONS
A1: Confirmed by the user's “y”: private repo david-kijko/homer-API, port 8767, hostname homer-api.kijko.nl, own ~/.homer-api key, read-only credential access, Claude CLI-owned refresh.
A2: Python 3.11 matches the host and Homer deployment conventions; one host process is sufficient.
A3: “Full compatible” means wire/SDK compatibility for all documented /v1 HTTP routes. Upstream OAuth scopes remain authoritative; current live probes show 200 models/files and native permission/not-found/auth errors for batches/skills/managed agents.
A4: The current documented Tunnels surfaces are HTTP management routes; no official current SDK path requires inbound WebSocket proxying. If Anthropic later documents a WebSocket /v1 route, that is a new transport requirement rather than silently implied HTTP support.
A5: Cloudflare's public edge imposes independent plan/timeout limits. The proxy can preserve Anthropic streaming semantics but cannot override Cloudflare limits; local :8767 remains the fidelity reference.

GAP IDENTIFICATION
Required research was executed with Exa and Firecrawl; saved under /tmp/homer-api-greenfield-research.

GAP TABLE
| Initial assumption | External source consulted | What the source actually says | Gap status |
|---|---|---|---|
| An Agent SDK wrapper could provide the full Anthropic API cheaply | https://github.com/dylanneve1/claude-sdk-proxy and its src/proxy/server.ts | The prior art is a 1,983-line request/response translation service centered on Messages/OpenAI/session behavior, not a full byte-transparent /v1 surface. | REFUTED — direct OAuth forwarding is smaller and more complete |
| A generic proxy library would reduce risk and code size | https://github.com/WSH032/fastapi-proxy-lib/blob/main/src/fastapi_proxy_lib/core/http.py | HTTP alone is 585 lines; WebSocket adds 808 lines and httpx-ws/private imports. Its generic URL/cookie/connection semantics exceed this fixed-origin requirement. | REFUTED — a fixed-origin module is smaller and more auditable |
| A new HTTPX client per request is harmless | https://www.python-httpx.org/async/ | HTTPX explicitly warns against client creation in a hot loop; one scoped AsyncClient preserves pooling. | REFINED — one lifespan client |
| StreamingResponse plus aiter_bytes is byte-transparent | https://www.python-httpx.org/async/ | aiter_raw is the method that avoids content decoding, and manual stream mode requires guaranteed Response.aclose(). | REFINED — aiter_raw plus generator finally/aclose |
| JSON error shape alone is enough | https://platform.claude.com/docs/en/api/errors | Every response has request-id; error bodies carry matching request_id. Limits differ: Messages/count 32 MB, batches 256 MB, files 500 MB. | REFINED — raw streaming, exact request-id, no local body buffer/limit |
| Messages/models/count represent the “full” API | official Anthropic Python SDK v0.116.0 and current docs inventory in /tmp/homer_sdk_contract_result.txt | 175 normalized documented /v1 paths and 243 method/path pairs include Admin, Compliance, Managed Agents, Skills, Files, and Tunnels beyond the regular SDK. | REFUTED — wildcard all-method routing |
| A transparent batch response needs no semantic edit | official SDK src/anthropic/resources/messages/batches.py:321-328 | results() follows the absolute results_url returned by Anthropic; unmodified it bypasses the custom base URL and sends the Homer key upstream. | REFINED — narrowly rebase results_url and Location |
| The API service should implement OAuth refresh itself | host Claude auth inspection and /tmp/claude_auth_recon_result.txt:127-139 | Claude CLI is the proven owner of reads/refresh; concurrent writers to one personal credential store are unverified. | REFUTED — API reads only and invokes safe-mode CLI refresh probe near expiry |
| One existing Cloudflare tunnel process is adequate isolation | existing /etc/cloudflared/homer-mcp.yml and Cloudflare Tunnel docs https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/ | A connector is an independent outbound process; sharing it couples restarts/configuration. | REFINED — separate named tunnel, credentials, config, unit |
| Cloudflare is transparent for arbitrarily long nonstream calls | https://developers.cloudflare.com/fundamentals/reference/connection-limits/ | Current proxied origin read timeout is 120 seconds for non-Enterprise zones; streaming activity avoids idle waits but the edge remains an external limit. | REFINED — verify SSE publicly and disclose edge constraint |

CONSTRAINTS AND CONTEXT
C-runtime: Python 3.11+, Linux host, uv-managed src-layout package.
C-deploy: One uvicorn process on loopback :8767, one separate named cloudflared process, systemd supervision.
C-storage: Only two existing-style files: generated API key under ~/.homer-api and read-only Claude credential JSON under ~/.claude; no DB.
C-perf: Stream requests/responses without buffering; one pooled AsyncClient; no target throughput requirement.
C-security: Public edge requires constant-time key comparison; caller secrets terminate locally; OAuth never leaves upstream Authorization; hop-by-hop/auth headers stripped; secrets excluded from logs/repo/tests.
C-user: Standalone repo and zero operational coupling to homer-mcp.

DESIGN OPTIONS CONSIDERED
| Option | Sketch | Pros | Cons | Rejected because |
|---|---|---|---|---|
| A | Agent SDK subprocess and reconstruct Anthropic responses | CLI owns auth | Loses arbitrary fields/routes; large translation layer; buffering/session semantics | Reject: violates R4/R5 |
| B | Fixed-origin ASGI/HTTPX streaming reverse proxy with read-only credential broker | Full wildcard surface; small; native errors/SSE/tools | Must carefully filter headers and broker token expiry | CHOSEN |
| C | Generic fastapi-proxy-lib | Existing HTTP/WebSocket machinery | Large dependency surface and generic behavior; auth/link rewrite still custom | Reject: violates D2 |
| D | Add route to homer-mcp | Reuses deployment | Couples failures/releases; user explicitly forbids | Reject: violates R1 |
| E (defer) | No endpoint | No risk | No requested behavior | Reject: violates all Rn |

Chosen option: B — It satisfies R1-R7 with a fixed upstream and five cohesive runtime modules; it keeps deployment/auth isolation while using official raw-stream primitives and needs only Starlette, HTTPX, and uvicorn.

MINIMAL ARCHITECTURE DECISION
Modules/files to create:
| Module | Purpose | Discharges | Why no smaller design suffices |
|---|---|---|---|
| src/homer_api/config.py | immutable settings and independent key lifecycle | R2,R3,C-security | CLI and app share paths/key operations |
| src/homer_api/credentials.py | read Claude token and ask Claude CLI to refresh without writing credentials | R6,INV4 | isolates the highest-risk shared boundary and enables no-network tests |
| src/homer_api/proxy.py | fixed-origin raw HTTP forwarding/header/link handling | R4,R5 | distinct transport boundary with MockTransport seam |
| src/homer_api/app.py | ASGI auth, health, routes, lifespan | R2,R3,R5 | owns public protocol and client lifetime |
| src/homer_api/__main__.py | serve/show-key/rotate-key CLI | R2,R3,R7 | required operator entrypoint |
| scripts/verify_anthropic.py | sanitized official-SDK behavioral proof | R3,R5,R7 | reusable user-visible acceptance command |
| tests/* | auth, credentials, proxy, official SDK contract | R3-R7 | separates risk surfaces while remaining small |
| systemd/* + cloudflared/*.example | isolated process/tunnel definitions | R1,R2 | reproducible deployment without touching Homer units |

Dependencies:
| Dependency | Version | Why | Could we do without? |
|---|---|---|---|
| starlette | >=0.49,<2 | small typed ASGI routing/middleware/streaming response | No; replacing ASGI plumbing exceeds 50 lines and raises risk |
| httpx | >=0.28,<1 | official manual async raw streaming + MockTransport test seam | No; stdlib lacks async streaming/pooling |
| uvicorn | >=0.30,<1 | production ASGI server already proven on host | No; writing server is out of scope |
| pytest/anyio | dev | async deterministic tests | No for R7 |
| anthropic==0.116.0 | dev/verification | current official client is the compatibility oracle | No for R3/R7 proof |
| ruff/mypy/build | dev | lint, strict types, package build gates | No for R7 |

INITIAL CONTRACTS AND INVARIANTS
IC1: GET /healthz — Pre: none; Post: 200 JSON service liveness; Errors: none from auth.
IC2: ANY /v1 or /v1/{path} — Pre: correct independent key in X-Api-Key or Bearer; Post: upstream method/raw path/query/body and native response are preserved except declared auth/hop/link transformations; Errors: Anthropic-shaped local 401/502/503 with request-id.
IC3: CLI show-key/rotate-key/serve — Pre: user owns ~/.homer-api; Post: key is created/rotated at 0600 or server starts on loopback; Errors: nonzero with no secret in logs.
INV1: Homer MCP repo, unit, port 8766, tunnel config/unit, key, and process are never modified or restarted.
INV2: The public key is never sent upstream; Claude OAuth is never returned downstream or logged.
INV3: Every opened upstream response is closed even on cancellation.
INV4: Homer API never writes ~/.claude/.credentials.json; only the Claude executable may refresh it.
INV5: Unknown/future /v1 HTTP paths are forwarded rather than locally rejected.
INV6: One AsyncClient exists per application lifespan.

CREATED SURFACE
| File | Purpose | Discharges |
|---|---|---|
| .github/workflows/ci.yml | push/PR lint,type,test,build | R7,D4 |
| .gitignore | exclude venv/cache/secrets | C-security |
| README.md | exact SDK, curl, deploy, limits, key instructions | R2,R3,R7 |
| pyproject.toml + uv.lock | package/dependency/tool contract | C-runtime,R7 |
| src/homer_api/__init__.py | package version | C-runtime |
| src/homer_api/config.py | settings/key | R2,R3,IC3 |
| src/homer_api/credentials.py | CLI-owned refresh broker | R6,INV4 |
| src/homer_api/proxy.py | streaming wildcard transport | R4,R5,INV2,INV3,INV5 |
| src/homer_api/app.py | auth/routes/lifespan | R2,R3,INV6 |
| src/homer_api/__main__.py | operator CLI | R2,R7,IC3 |
| scripts/verify_anthropic.py | official SDK acceptance | R3,R5,R7,D4 |
| tests/test_auth.py | auth/health/error contract | R2,R3 |
| tests/test_credentials.py | valid/expired/CLI ownership | R6 |
| tests/test_proxy.py | raw multipart/SSE/binary/errors/link/cancel | R4,R5 |
| tests/test_official_sdk.py | normal official client against app | R3,R7 |
| systemd/homer-api.service | isolated API unit | R1,R2 |
| systemd/cloudflared-homer-api.service | isolated connector unit | R1,R2 |
| cloudflared/homer-api.yml.example | fixed independent ingress | R1,R2 |

REQUIREMENT → CODE MAPPING
R1 → systemd assets and separate package/repo, demonstrated by deployment/process regression probes. Inference: spec-decomposition.
R2 → config.py, app.py, units/tunnel template, NT1/NT-smoke. Inference: new-construction.
R3 → app auth + official SDK test/verify script, NT2/NT-smoke. Inference: spec-decomposition.
R4 → proxy wildcard raw URL/method/body, NT3. Inference: new-construction.
R5 → proxy response generator/header/link logic, NT4-NT7. Inference: new-construction.
R6 → credentials broker read + Claude subprocess only, NT8/NT9. Inference: invariant-establishment.
R7 → CI/tool config/tests/script/docs, all NTs and build commands. Inference: spec-decomposition.

VERIFICATION SCAFFOLD
Test framework: pytest with AnyIO and HTTPX MockTransport; ties directly to async ASGI and provides no-network fixtures.
Smoke command: HOMER_API_BASE_URL=https://homer-api.kijko.nl HOMER_API_KEY_FILE=~/.homer-api/api-key.txt uv run --with anthropic==0.116.0 python scripts/verify_anthropic.py
Build/type/lint: uv run ruff check .; uv run mypy src tests scripts; uv run pytest -q; uv build.
Fixture strategy: temporary key/credential files, injected credential refresh runner, MockTransport raw byte streams, Starlette TestClient, official SDK using TestClient transport.
Fresh clone: uv sync --all-groups && uv run pytest -q && uv run homer-api show-key && uv run homer-api serve.

NEW TEST OBLIGATIONS
NT1: health public and all other paths protected; correct/wrong X-Api-Key and Bearer — R2/R3.
NT2: official Anthropic client with base_url origin parses messages/models and typed errors through app — R3/R7.
NT3: arbitrary stable/beta/Admin/Compliance/Tunnel path, method, raw query, multipart boundary/body/header pass-through — R4.
NT4: native named SSE chunks arrive raw and upstream closes — R5.
NT5: JSONL/binary/compressed bytes, status, request-id, duplicate end-to-end headers pass — R5.
NT6: native upstream error body is byte-identical — R5.
NT7: batch results_url/Location are rebased while unrelated text is unchanged — R5.
NT8: valid credential read performs no subprocess and never writes — R6.
NT9: expired credential invokes safe-mode Claude refresh runner, re-reads a valid token, and source file changes only through injected runner — R6.
NT10: full lint/type/test/build CI workflow — R7.
NT-smoke: official SDK models/count/nonstream/SSE/tools/negative-auth against local and public URL plus unchanged Homer /healthz/capabilities — R1-R7.

COUNTEREXAMPLE / SUFFICIENCY CHECK
R1: If either unit points at :8766 or the Homer tunnel ID, isolation fails. Tests/file inspection plus process/listener probes require distinct names/:8767/tunnel UUID.
R2: If the service accepts Homer's key or binds 0.0.0.0, the approved boundary fails. Config defaults and deployment probes require separate path/loopback.
R3: Current SDK sends X-Api-Key and appending /v1 to base_url creates /v1/v1/messages. README/test use the origin and path-scoped standard auth.
R4: Any allow-list has a concrete counterexample among the 175 current paths. A single fixed-origin wildcard handles all HTTP method/path inputs; live entitlement may still deny them upstream by explicit non-goal.
R5: aiter_bytes would decode content; omitted finally would leak connections; untouched results_url bypasses custom base. Tests cover all three counterexamples.
R6: Direct refresh code could race Claude/Homer and break shared auth. The broker has no write function and can only run the installed Claude CLI before re-reading.
R7: Unit-only evidence cannot prove the tunnel/SDK. The committed verifier plus live commands produce literal, sanitized output.
Less check: stdlib HTTP server/client would require more code; generic proxy/Agent SDK adds more concepts; no DB/cache/queue/schema/plugin/container is created.

ADVERSARIAL CHECK
1. Premature abstraction: CredentialBroker and Proxy are single-use but each owns a separately dangerous IO boundary and needs injection for no-network tests; other logic remains functions.
2. Unjustified dependency: only three runtime deps remain; removing any requires implementing >50 lines of protocol/server behavior. Generic proxy/httpx-ws are rejected.
3. Untestable boundary: all auth/refresh/transport behavior uses path/runner/MockTransport injection and runs without network/DB/LLM; only NT-smoke uses real external state.

UI_BEHAVIOR_AFFECTING: no

FORMAL CONCLUSION
By D1 (SUFFICIENT):          yes — every R1-R7 maps to created code and NTs.
By D2 (MINIMAL):             yes — every file/dependency maps to a declared requirement or invariant.
By D3 (INTERNALLY COHERENT): yes — fixed-origin streaming, read-only credentials, isolated deployment, and tests align.
By D4 (VERIFIABLE):          yes — exact official-SDK local/public smoke command exists.

Plan is READY TO IMPLEMENT: YES
