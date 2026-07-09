Design a precise landscape architecture diagram for a new standalone backend called “homer-API.” Use a white background, dark navy outlines, teal for streamed data, amber for secret boundaries, and gray for explicitly untouched infrastructure. It should look like an engineering review artifact, not marketing art.

Start on the left with an ordinary Anthropic SDK. Show only its normal configuration: base_url=https://homer-api.kijko.nl and api_key=the independent Homer API key. Route it through a dedicated Cloudflare named tunnel into a dedicated loopback listener at 127.0.0.1:8767. Both the tunnel process and uvicorn process must be inside a bold “standalone homer-API deployment” boundary.

Inside the service, show an API-key gate that accepts X-Api-Key or Bearer and compares against ~/.homer-api/api-key.txt. Put a clear stop marker here: the caller key terminates and is stripped. Then show a fixed-origin /v1 wildcard streaming proxy. Its forward flow must list method, raw path/query, multipart or arbitrary body chunks, Anthropic version/beta/custom headers. Its return flow must split into native JSON/errors with request-id, SSE named events, JSONL/binary bytes, and response links. Mark only results_url and Location as being rebased to homer-api.kijko.nl.

Beside the proxy, show a small read-only Credential Broker. It reads ~/.claude/.credentials.json. If the token is near expiry, it invokes the installed Claude CLI in safe, non-persistent, no-tools print mode; the CLI—not homer-API—may refresh the credential file. Draw the OAuth bearer traveling only from broker to api.anthropic.com. No secret arrow may point back to the caller.

On the far right, show api.anthropic.com as an external authority. State that every current/future HTTP /v1 route is transport-forwarded, while OAuth scopes decide whether Files, Batches, Admin, Compliance, Skills, Managed Agents, or Tunnels are actually authorized. Native permission errors return unchanged.

At the bottom, draw homer-mcp as a separate gray island containing port 8766, its own key, its existing service, and its existing tunnel. Put a large label “UNTOUCHED: no imports, config edits, restart, shared listener, key, or tunnel process.” There must be no arrows between homer-mcp and homer-API. Both may read the machine’s Claude-owned credential state, but only the Claude CLI owns refresh writes.

INVARIANTS THE PICTURE MUST ENCODE:
- Separate repo, process, port 8767, key file, tunnel UUID/config/unit, logs, and deployment lifecycle.
- Homer API binds loopback; the public edge is the dedicated named tunnel.
- The public API key never reaches Anthropic and OAuth never reaches callers.
- Request and response bodies stay streaming/raw; the service does not translate Anthropic schemas.
- Every upstream response is closed on completion or cancellation.
- Claude CLI alone writes the shared credential file.
- Product entitlement errors are not hidden or emulated.

WHAT THE PICTURE MUST NOT IMPLY:
- No route or code inside homer-mcp; no shared tunnel process; no restart of Homer MCP.
- No GPT/OpenAI translation, Agent SDK response reconstruction, database, cache, queue, container, plugin system, or UI.
- No claim that Admin/Compliance/Batches/Skills/Managed Agents/Tunnels succeed with subscription OAuth.
- No direct OAuth refresh grant implemented by homer-API.
- No inbound WebSocket path unless the official Anthropic HTTP specification later adds one; this contract covers documented HTTP /v1 routes and SSE/JSONL streams.

TARGETED CORRECTION FOR THE FINAL RENDER:
- Do not use any blanket statement that “secrets are not forwarded upstream.” That is false because the Claude OAuth bearer must be sent to api.anthropic.com.
- If a secret-flow banner is shown, its exact meaning must be: “Homer API caller key stays local; Claude OAuth bearer goes only to api.anthropic.com.”
