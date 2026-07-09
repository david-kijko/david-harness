Create a clean technical architecture infographic for a backend change, landscape 16:9, crisp readable labels, restrained blue/teal palette with one amber security boundary. The picture should explain an existing service rather than advertise a new product.

On the left, show an untouched “Normal Anthropic SDK” box configured with two ordinary values: base_url = https://homer.kijko.nl and api_key = Homer key. Its arrow crosses an amber “Existing Homer caller-auth boundary” where either X-Api-Key (new SDK-compatible form) or the already-supported Bearer form is checked against the same existing ~/.homer-mcp/api-key.txt. Explicitly mark that the Homer key stops here and never goes upstream.

In the center, enclose the only code change inside the existing “homer-mcp :8766” service. Show a wildcard /v1/{path} router feeding a small streaming reverse-proxy component. The proxy passes method, raw path/query, JSON or multipart body stream, and Anthropic headers without interpreting the model request. Beside it, show a narrow credential provider reading ~/.claude/.credentials.json as david, refreshing near expiry, and atomically preserving mode 0600. Its OAuth bearer token flows only rightward to upstream. Also show the existing MCP mount, /api/v1 REST routes, /healthz, and OAuth connector paths as gray untouched lanes tagged “still satisfied.”

On the right, show the external api.anthropic.com boundary. Return arrows must split into four visibly distinct channels: JSON/errors with request-id, native SSE named events, binary or JSONL downloads, and response links. Only the batch results_url/Location link channel is rebased back to homer.kijko.nl so a normal SDK does not bypass the proxy. Make it visually obvious that the proxy does not translate Anthropic schemas or invent responses.

Below, show the already-existing named Cloudflare tunnel as an unchanged pipe between homer.kijko.nl and localhost:8766. Add an explicit scope note: transport coverage includes every current and future /v1 path, but upstream OAuth entitlements remain authoritative; unsupported batches/skills/managed-agents errors pass through unchanged.

INVARIANTS THE PICTURE MUST ENCODE:
- One existing Homer key and one existing tunnel; no new daemon, port, key store, or tunnel.
- Caller key terminates at Homer; Claude OAuth never returns to callers.
- SSE and binary payloads remain streaming/raw, not buffered or translated.
- Existing MCP/REST/health/OAuth connector routes remain operational and outside the new wildcard lane.
- The only semantic response edit is safe rebasing of upstream follow-up links.
- Change-surface boundary contains anthropic_proxy.py and small server/auth/lifespan wiring only.

WHAT THE PICTURE MUST NOT IMPLY:
- Do not depict GPTAuthWrapper, ClaudeAuthWrapper, OpenAI translation, request schema conversion, a database migration, a container, or a Quick Tunnel.
- Do not imply Homer grants Anthropic product permissions that the Claude OAuth account lacks.
- Do not show the public Homer key being forwarded to Anthropic.
- Do not show edits to SessionManager or replacement of the existing Claude CLI dispatch path.
- Do not show browser UI or human approval flows.
