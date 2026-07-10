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
I want to make some changes to hephaestus-mcp so that it has a permanent url and the model can be upgraded to gpt-5.6-sol (all effort levels) please update gdrive KEYMAKER.env when finished and provide the credentials for a MCP host to make a connection ensure it gives full access to the the hands on this server

SPEC DECOMPOSITION (atomic, testable)
R1: The public MCP endpoint is a stable named HTTPS URL rather than a rotating quick-tunnel URL.
R2: gpt-5.6-sol is available and becomes the default model without removing existing gpt-5.5/gpt-5.4 callers.
R3: gpt-5.6-sol accepts every effort advertised by the live Codex registry: low, medium, high, xhigh, max, ultra.
R4: An authenticated MCP caller has explicit full-server hands-on access: / is an accepted work directory and dangerous mode is enabled. Bearer authentication remains mandatory.
R5: The canonical Google Drive KEYMAKER.env is updated in place with the permanent endpoint plus current model/effort/access metadata while preserving the existing matching bearer token aliases.
R6: The user receives the exact Streamable HTTP host configuration and bearer credential needed to connect.
OUT OF SCOPE: replacing bearer auth, changing OAuth semantics, rotating the existing key, changing the separate tijmen service, or creating a new DNS zone/tunnel because the named tunnel and DNS already exist.

EXISTING PATTERN SURVEY
| Concern | Hypothesis: pattern exists? | Evidence | Still preferred? | Decision |
|---|---|---|---|---|
| Bearer auth | yes | src/hephaestus_mcp/config.py:97-116 stores one 0600 API key; src/hephaestus_mcp/server.py:973-1015 compares Authorization Bearer with that key | yes | REUSE; do not add another credential system |
| OAuth discovery | yes | src/hephaestus_mcp/server.py:719-955 implements discovery, DCR, PKCE and token exchange; lines 959-1015 gates public routes | yes | PRESERVE unchanged |
| Model/effort selection | yes | src/hephaestus_mcp/config.py:37-44 owns defaults; src/hephaestus_mcp/server.py:194-250 validates dispatch arguments; src/hephaestus_mcp/session_manager.py:381-398 forwards model/effort | yes, but global effort validation is insufficient for model-specific levels | EXTEND with registry-grounded per-model effort mapping |
| Path access | yes | src/hephaestus_mcp/path_guard.py:61-92 applies allow/deny roots; src/hephaestus_mcp/config.py:15-27 defaults conservatively | yes | REUSE; enable a deployment-only full-server override rather than weakening safe library defaults |
| Dangerous mode | yes | src/hephaestus_mcp/config.py:69 detects HEPHAESTUS_MCP_ALLOW_DANGEROUS; src/hephaestus_mcp/server.py:202-209 rejects disabled dangerous dispatch | yes | EXTEND with explicit full-server deployment flag |
| Permanent tunnel | live host pattern exists but repo installer is stale | systemd/cloudflared-hephaestus-mcp.service:2,8 uses a quick tunnel; install.sh:37-47 scrapes trycloudflare; live /etc/cloudflared/hephaestus-mcp.yml maps heph.kijko.nl to 8765 | named tunnel is preferred | REPLACE install path with named unit/config while leaving credentials out of git |
| Drive secret store | yes | Drive file id 1TTzfceBSVcIHGKh0DdJuIa5ft4naG2xB is the single exact KEYMAKER.env result; MCP_HEPHAESTUS currently points at trycloudflare while three token aliases match the host key | yes | UPDATE same file id and read back |

INTEGRATION POINTS
IP1: src/hephaestus_mcp/config.py:30-70 — resolved runtime configuration consumed by every request.
IP2: src/hephaestus_mcp/server.py:93-136 and 194-250 — MCP arguments validated before path guard/session dispatch.
IP3: src/hephaestus_mcp/session_manager.py:375-398 and 498-513 — selected values become the actual Hephaestus/Codex process arguments.
IP4: systemd/hephaestus-mcp.service:6-13 — deployment environment selects full-server mode.
IP5: install.sh:24-69 and systemd tunnel unit — installer selects permanent ingress.
IP6: Google Drive raw file id 1TTzfceBSVcIHGKh0DdJuIa5ft4naG2xB — canonical external client config.

INVARIANTS THAT MUST BE PRESERVED
INV1: Every non-public endpoint requires the exact bearer token. Evidence: src/hephaestus_mcp/server.py:973-1015. Preservation: no auth middleware or public path changes; live no-auth 401 is retested.
INV2: OAuth discovery/PKCE remains available for Claude connectors. Evidence: src/hephaestus_mcp/server.py:719-955 and tests/test_oauth.py:62-176. Preservation: existing tests remain PASS_TO_PASS.
INV3: Legacy model callers remain accepted at their four registry-supported efforts. Evidence: src/hephaestus_mcp/config.py:37-41 currently advertises gpt-5.5/gpt-5.4; live model cache lists low/medium/high/xhigh for each. Preservation: retain both and validate per model.
INV4: Safe defaults remain conservative unless the systemd deployment explicitly opts into full-server access. Evidence: src/hephaestus_mcp/config.py:15-27. Preservation: override only when HEPHAESTUS_MCP_FULL_SERVER_ACCESS=1.
INV5: The permanent tunnel credential JSON is never committed. Evidence: live YAML refers to an external 0400 credential file. Preservation: repository YAML stores only tunnel ID, hostname, route and credential path.
INV6: Existing Drive key aliases continue to match the host key. Evidence: redacted comparison showed all three aliases match. Preservation: update content without rotating or rewriting token values and verify hashes/equality after upload.

CHANGE SURFACE
| File | New / Modified | Approx lines | Discharges Rn |
|---|---|---:|---|
| src/hephaestus_mcp/config.py | Modified | 25 | R2, R3, R4 |
| src/hephaestus_mcp/server.py | Modified | 30 | R2, R3, R4 |
| tests/test_config.py | New | 70 | R2, R3, R4 |
| tests/test_oauth.py | Modified | 15 | R2, R3 |
| systemd/hephaestus-mcp.service | Modified | 3 | R4 |
| systemd/cloudflared-hephaestus-mcp-named.service | New | 15 | R1 |
| cloudflared/hephaestus-mcp.yml | New | 10 | R1 |
| install.sh | Modified | 35 | R1, R6 |
| Drive KEYMAKER.env (same external file id) | Modified | small section | R5, R6 |

REQUIREMENT → CODE MAPPING
R1 → named tunnel unit/config plus install.sh permanent URL because the installed process will route heph.kijko.nl to localhost:8765; inference: pattern-reuse.
R2 → Config defaults and dispatch function default because capability/OpenAPI/tool calls derive from them and SessionManager forwards the chosen slug; inference: invariant-preserving construction.
R3 → supported effort constants, model-specific validation, OpenAPI/capabilities metadata and six live MCP dispatches; inference: spec-decomposition plus registry-grounded construction.
R4 → explicit HEPHAESTUS_MCP_FULL_SERVER_ACCESS config override and systemd opt-in because path_guard receives / with no denylist and dangerous dispatch becomes accepted; inference: invariant-preserving construction.
R5 → in-place Drive replacement and fetch readback because the exact canonical file id remains unchanged while its endpoint/model metadata changes; inference: pattern-reuse.
R6 → installer output and final handoff provide URL, transport and Authorization header; inference: spec-decomposition.

BACKWARD-COMPATIBILITY TRACE
Existing callers:
C1: server.py dispatch callers passing gpt-5.5/gpt-5.4 with low/medium/high/xhigh remain accepted through per-model mapping: STILL SATISFIED.
C2: read_files callers omitting effort get high, now on the new default model: intentionally upgraded and still valid.
C3: static bearer clients keep the same host token: STILL SATISFIED.
C4: Claude OAuth discovery clients keep the same routes and flow: STILL SATISFIED.
C5: installer callers gain a prerequisite for the existing named-tunnel credential/config; appropriate for this host-specific permanent deployment.
PASS_TO_PASS tests:
T1: tests/test_oauth.py:62-176 auth/discovery/code flow must remain green.
T2: tests/test_session_manager.py:60-137 dispatch output and completion status must remain green.

NEW TEST OBLIGATIONS
NT1: config defaults test — demonstrates R2/R3 by asserting default gpt-5.6-sol and exactly six registry efforts. Runnable: pytest -q tests/test_config.py.
NT2: model-specific effort test — demonstrates R3/backward compatibility by proving max/ultra only for gpt-5.6-sol while legacy models retain four levels. Runnable: pytest -q tests/test_config.py.
NT3: full-server environment override test — demonstrates R4 by resolving allowed_dirs ['/'], read_only_root '/', denied_dirs [], dangerous true only under the explicit flag. Runnable: pytest -q tests/test_config.py.
NT4: live no-auth/bearer capabilities and MCP initialize — demonstrates R1/R4/R6. Runnable: curl against https://heph.kijko.nl.
NT5: six live MCP dispatches — demonstrates R2/R3 by calling dispatch_hephaestus with gpt-5.6-sol at low, medium, high, xhigh, max and ultra, then polling actual responses.
NT6: harmless root-capability dispatch — demonstrates R4 with sudo -n id -u returning 0 through the public MCP API.
NT7: Drive search/fetch readback — demonstrates R5 by printing only endpoint/model/effort/access fields and equality checks for bearer aliases.
NT8: bash -n install.sh plus systemd-analyze verify on both units — demonstrates R1 deployment syntax.

COUNTEREXAMPLE / SUFFICIENCY CHECK
R1 → A quick-tunnel process restart changes the hostname and violates permanence. The named tunnel binds DNS names to a durable tunnel ID, and live DNS/health checks cover that partition.
R2 → If only Config.default_model changes but runtime config retains gpt-5.5, live capabilities stay stale. Deployment explicitly migrates ~/.hephaestus-mcp/config.toml and restarts the actual service.
R3 → A single global effort list lets gpt-5.5 accept max and fail downstream. Per-model intersection prevents this; six actual gpt-5.6-sol calls cover every advertised value.
R4 → Merely enabling --dangerous does not let dir='/' pass path_guard. Full-server override changes all three path inputs and a live root probe proves the end-to-end path.
R5 → Updating a duplicate Drive file would leave canonical clients stale. Exact-name search must return one file and update preserves id 1TTzfceBSVcIHGKh0DdJuIa5ft4naG2xB.
R6 → A URL and token without the Authorization scheme is not a usable MCP config. Handoff includes transport, URL and complete header syntax.
Coverage: auth rejection, bearer success, OAuth PASS_TO_PASS, legacy model compatibility, each new effort, root working directory, root privilege, named ingress, and Drive readback are covered.

UI_BEHAVIOR_AFFECTING: no

FORMAL CONCLUSION
By D1 (SUFFICIENT): yes — every Rn has mapped code/external update and a runnable NTn.
By D2 (MINIMAL): yes — every change-surface row maps directly to R1-R6.
By D3 (COMPATIBLE): yes, conditional on PASS_TO_PASS and live probes; legacy models/auth are preserved.
By D4 (VERIFIABLE): yes — every Rn has direct command/tool behavior.

Plan is READY TO IMPLEMENT: YES
