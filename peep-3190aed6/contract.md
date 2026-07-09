SEMI-FORMAL BROWNFIELD CONSTRUCTION CERTIFICATE

DEFINITIONS
D1: SUFFICIENT iff every Rn has at least one mapped change in CHANGE SURFACE
    AND at least one demonstrating NTn in NEW TEST OBLIGATIONS.
D2: MINIMAL iff every row in CHANGE SURFACE cites at least one Rn.
D3: COMPATIBLE iff every existing caller in BACKWARD-COMPATIBILITY TRACE
    is preserved or its breakage is explicitly justified, AND every
    PASS_TO_PASS test on the change surface remains green by trace.
D4: VERIFIABLE iff every Rn maps to at least one NTn whose pass/fail can
    be observed by running a concrete command.

SPEC (verbatim from the user — do not paraphrase)
See spec.txt; its byte-exact contents are embedded above this contract in the archive.

SPEC DECOMPOSITION (atomic, testable)
R1: Add the API endpoint to the existing homer-mcp Starlette service and existing homer.kijko.nl named tunnel; create no standalone ClaudeAuthWrapper daemon or second tunnel.
R2: A normal current Anthropic SDK configured with base_url=https://homer.kijko.nl and Homer's existing key must authenticate through the SDK's standard X-Api-Key header; existing Authorization: Bearer Homer callers must remain valid.
R3: Cover the current full Anthropic SDK HTTP control surface by transparently forwarding every method and subpath under /v1/, including query strings, JSON, multipart uploads, arbitrary request bodies, binary/JSONL downloads, and future /v1 additions without local schema narrowing.
R4: Replace the caller's Homer credential at the trust boundary with the host user's Claude OAuth access token, merge the required OAuth beta header, proactively refresh expiring OAuth credentials, persist rotated credentials atomically with mode 0600, and never return either secret.
R5: Preserve upstream status, request-id and other end-to-end headers, Anthropic JSON error bodies, SSE chunk framing, binary bytes, and cancellation; rewrite only upstream absolute batch results_url/Location links that would otherwise bypass the configured Homer base URL.
R6: Preserve all existing Homer MCP, REST, OAuth connector, health, OpenAPI, session, and tunnel behavior.
R7: Ground the compatibility claim in the current official Anthropic Python SDK/API inventory and prove both generic transport behavior and real local/public SDK behavior (models, token count, non-stream message, named SSE events, forced tool use, and negative auth).

OUT OF SCOPE: Fabricating product entitlements absent from this Claude OAuth account. Live upstream probes show models and files are authorized, while batches, skills, and managed agents currently return native 403/404/401 responses. The proxy must relay those responses exactly rather than emulate unavailable products.

EXISTING PATTERN SURVEY
| Concern | Hypothesis: pattern exists? | Evidence (file:line) | Still preferred? | Decision |
|---|---|---|---|---|
| Public service/tunnel | Homer already owns the stable listener and tunnel | scripts/homer-tmux.sh:4-9,69-82; /etc/cloudflared/homer-mcp.yml:1-8 | yes | REUSE existing port 8766 and named ingress; no tunnel code |
| Caller authentication | One middleware owns Homer's generated bearer key | src/homer_mcp/config.py:120-127; src/homer_mcp/server.py:1049-1098 | yes, extended only for SDK header compatibility | EXTEND middleware for X-Api-Key on /v1 while retaining bearer behavior elsewhere |
| Route composition | Explicit REST routes precede catch-all FastMCP mount | src/homer_mcp/server.py:1113-1148 | yes | EXTEND with /v1/{path:path} before Mount("/") |
| Streaming HTTP client | No upstream HTTP proxy implementation exists | search for StreamingResponse/httpx/request.stream found no implementation; src/homer_mcp/server.py:1-23 | n/a | NEW focused module; existing SessionManager CLI subprocess is not a byte-preserving HTTP surface |
| Claude authentication | Homer dispatches the installed Claude CLI, but has no raw API token provider | src/homer_mcp/config.py:46-61; tests/test_model_selection.py:99-110 | CLI pattern cannot preserve native API fields/SSE | NEW minimal OAuth token provider reading the same host credential file |
| SDK wire contract | Official SDK sends X-Api-Key and anthropic-version | /tmp/anthropic-sdk-python-v0.116.0/src/anthropic/_client.py:334-365 | authoritative | REUSE the official client unchanged for behavioral verification |
| Full endpoint inventory | Official SDK v0.116.0 contains stable and beta /v1 routes, multipart upload, batches and streams | /tmp/anthropic-sdk-python-v0.116.0/api.md:20-1201; /tmp/anthropic-sdk-python-v0.116.0/src/anthropic/resources/beta/files.py:314-340 | authoritative | FORWARD wildcard rather than reimplement 90 observed method/path templates |
| Existing test style | Starlette TestClient fixtures patch config paths and exercise real middleware | tests/test_oauth.py:18-52,62-91 | yes | REUSE fixture conventions; add focused proxy tests |

INTEGRATION POINTS
IP1: src/homer_mcp/server.py:64-69 — build_app owns config, API key, and service dependencies — instantiate one lifecycle-managed Anthropic proxy.
IP2: src/homer_mcp/server.py:1049-1098 — BearerAuthMiddleware owns the trust boundary — recognize standard X-Api-Key only for /v1 and emit Anthropic-shaped auth errors there.
IP3: src/homer_mcp/server.py:1103-1111 — lifespan owns async resource lifetime — enter/close the upstream httpx client without affecting MCP lifespan.
IP4: src/homer_mcp/server.py:1113-1141 — route ordering controls the FastMCP catch-all — insert /v1 route before Mount("/").
IP5: src/homer_mcp/config.py:120-127 — existing Homer key remains the sole caller credential; no second secret store.

INVARIANTS THAT MUST BE PRESERVED
INV1: Every non-public Homer route requires the current Homer key. Evidence: src/homer_mcp/server.py:1063-1098. Preservation: /v1 adds an equivalent X-Api-Key representation; all other paths retain exact bearer-only evaluation and failure response.
INV2: Health/OpenAPI and enabled OAuth discovery remain public while disabled OAuth endpoints remain 404. Evidence: src/homer_mcp/server.py:1051-1070. Preservation: no public-path membership changes.
INV3: Existing route resolution reaches Homer REST routes before the FastMCP mount. Evidence: src/homer_mcp/server.py:1113-1141. Preservation: /v1 is inserted in that explicit list before the unchanged Mount.
INV4: The Homer key file is generated once and protected with 0600. Evidence: src/homer_mcp/config.py:120-127. Preservation: caller auth reuses it and never writes it.
INV5: Claude credentials remain user-owned, complete JSON and 0600 even after refresh. Evidence: host inspection of ~/.claude/.credentials.json plus the schema used by the running Claude CLI; preservation obligation: same-directory atomic replace, full-document preservation, rotated access/refresh fields only, explicit chmod 0600.
INV6: Existing MCP lifecycle is entered exactly once. Evidence: src/homer_mcp/server.py:1103-1111. Preservation: proxy context nests around the existing mcp_app lifespan rather than replacing or duplicating it.

CHANGE SURFACE
| File | New / Modified | Approx lines | Discharges Rn |
|---|---|---:|---|
| pyproject.toml | Modified | 1 | R3, R5 (direct httpx dependency) |
| uv.lock | Modified/generated | dependency metadata only | R3, R5 |
| src/homer_mcp/anthropic_proxy.py | New | 220 | R3, R4, R5 |
| src/homer_mcp/server.py | Modified | 45 | R1, R2, R6 |
| tests/test_anthropic_proxy.py | New | 300 | R2-R7 |

REQUIREMENT → CODE MAPPING
R1 → planned src/homer_mcp/server.py route/lifespan integration at existing build_app and route table (current lines 64-69,1103-1141); inference type: pattern-reuse.
R2 → planned BearerAuthMiddleware extension at src/homer_mcp/server.py:1049-1098 plus NT1/NT2; inference type: invariant-preservation.
R3 → planned AnthropicProxy.forward in src/homer_mcp/anthropic_proxy.py:new, using raw ASGI path/query/body stream and wildcard methods, plus NT3/NT4/NT5; inference type: new-construction.
R4 → planned ClaudeOAuthCredentials in src/homer_mcp/anthropic_proxy.py:new, plus NT6/NT7; inference type: new-construction.
R5 → planned response relay/rewriter in src/homer_mcp/anthropic_proxy.py:new, plus NT4/NT5/NT8; inference type: spec-decomposition.
R6 → minimal server integration only and PASS_TO_PASS suite tests/test_oauth.py plus tests/test_model_selection.py; inference type: invariant-preservation.
R7 → official SDK snapshot /tmp/anthropic-sdk-python-v0.116.0 at tag v0.116.0, generic proxy tests, and live SDK proof script; inference type: spec-decomposition.

BACKWARD-COMPATIBILITY TRACE
Existing callers of changed code:
  C1: FastMCP clients hit /mcp with Authorization: Bearer and expect OAuth metadata on 401 (tests/test_oauth.py:62-68). After change: STILL SATISFIED; non-/v1 auth branch is unchanged.
  C2: OAuth connector flow exchanges access_token equal to the Homer key and then calls REST (tests/test_oauth.py:94-150 and following). After change: STILL SATISFIED; token issuance and bearer REST auth are unchanged.
  C3: REST callers use /api/v1/* bearer auth (tests/test_model_selection.py:113-142,145-170). After change: STILL SATISFIED; path is outside /v1 wildcard and route ordering remains explicit.
  C4: systemd/tmux starts python -m homer_mcp serve from ROOT_DIR (scripts/homer-tmux.sh:4-9,69-82). After change: STILL SATISFIED; entrypoint and port remain unchanged.
Existing tests touching the change surface (PASS_TO_PASS):
  T1: tests/test_oauth.py — MUST REMAIN GREEN because public/OAuth/bearer branches are preserved.
  T2: tests/test_model_selection.py — MUST REMAIN GREEN because dispatch and OpenAPI behavior are untouched.
  T3: tests/test_cloud_dispatch.py, tests/test_cloud_daemon_launch.py — MUST REMAIN GREEN because SessionManager is untouched.

NEW TEST OBLIGATIONS
NT1: test_anthropic_route_accepts_standard_x_api_key — R2; correct X-Api-Key reaches proxy. Runnable: uv run --with pytest pytest -q tests/test_anthropic_proxy.py::test_anthropic_route_accepts_standard_x_api_key
NT2: test_anthropic_auth_failure_uses_native_error_shape — R2/R5; missing/wrong key returns 401 authentication_error and request-id while existing bearer tests remain green. Runnable: same file test.
NT3: test_proxy_preserves_method_raw_path_query_headers_and_multipart_body — R3; arbitrary beta file upload is byte-identical except auth/hop headers. Runnable: same file test.
NT4: test_proxy_streams_raw_sse_and_binary_chunks — R3/R5; named SSE framing and compressed/binary bytes are not decoded/re-encoded. Runnable: same file test.
NT5: test_proxy_relays_status_duplicate_end_to_end_headers_and_native_error — R3/R5; upstream errors/status/request-id pass unchanged. Runnable: same file test.
NT6: test_valid_claude_oauth_is_loaded_without_refresh — R4; token comes from 0600 host-schema fixture and is absent from response/logs. Runnable: same file test.
NT7: test_expiring_claude_oauth_refreshes_and_atomically_persists_rotation — R4; exact refresh grant, rotated fields, preserved document, and 0600. Runnable: same file test.
NT8: test_batch_results_url_and_location_are_rebased_to_homer — R5; official SDK follow-up cannot bypass proxy. Runnable: same file test.
NT9: full existing suite — R6. Runnable: uv run --with pytest pytest -q
NT10: current official Anthropic SDK live proof — R1/R2/R3/R5/R7; base_url origin plus Homer key runs models, count_tokens, nonstream message, streaming event sequence, forced tool use, negative auth locally and through homer.kijko.nl. Runnable: uv run --with anthropic==0.116.0 python /tmp/verify_homer_anthropic.py

COUNTEREXAMPLE / SUFFICIENCY CHECK
R1 → Soundness sketch: only build_app/lifespan/routes change inside the existing process; no new listener or tunnel file appears in CHANGE SURFACE. Existing systemd/tunnel evidence fixes the integration target.
R2 → Counterexample: official SDK emits X-Api-Key, while current middleware only parses Authorization (src/homer_mcp/server.py:1071-1077); without NT1 the SDK always receives 401. Plan revised to add path-scoped X-Api-Key support.
R3 → Counterexample: enumerating only messages/models would omit current files, batches, skills, sessions, vaults, agents and future paths evidenced by api.md:20-1201. Plan uses /v1/{path:path}, all relevant HTTP methods, raw request streaming, and generic transport partitions.
R4 → Counterexample: merely reading accessToken fails after expiresAt. Plan adds proactive refresh with a single async lock, concurrent-change re-read, and atomic full-document replacement. Unexercised external race: Claude CLI does not promise to honor Homer's lock; compare-before-replace and re-read reduce but cannot formally eliminate a last-instruction race.
R5 → Counterexample: official batch results() follows batch.results_url as an absolute URL (/tmp/anthropic-sdk-python-v0.116.0/src/anthropic/resources/messages/batches.py:321-328); byte-transparent JSON would bypass Homer and send the Homer key upstream. Plan narrowly rebases results_url and Location only. SSE and binary partitions remain byte-raw.
R6 → Soundness sketch: no SessionManager/config/tunnel behavior changes; auth branch is conditional on /v1; existing PASS_TO_PASS suite exercises the preserved branches.
R7 → Counterexample: unit tests against invented payloads would not prove SDK compatibility. Plan pins the current official v0.116.0 client for user-level local and public execution and records literal outputs.
Coverage partitions: authorized/unauthorized; X-Api-Key/Bearer; JSON/multipart/empty/raw stream; JSON/SSE/JSONL/binary; success/4xx/5xx; valid/expiring credential; local/public. Product entitlement success for batches/skills/managed agents is untestable with the present OAuth scopes and is explicitly out of scope; their native error relay is tested.

UI_BEHAVIOR_AFFECTING: no

FORMAL CONCLUSION
By D1 (SUFFICIENT): yes — every R1-R7 has mapped code and at least one NT.
By D2 (MINIMAL):    yes — every changed file maps directly to R1-R7; no standalone wrapper/tunnel or unrelated refactor.
By D3 (COMPATIBLE): yes — all named callers remain on unchanged paths/branches and the complete existing suite is PASS_TO_PASS.
By D4 (VERIFIABLE): yes — every requirement has a concrete unit or live SDK command.

Plan is READY TO IMPLEMENT: YES
