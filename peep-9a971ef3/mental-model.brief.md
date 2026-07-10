# Mental model brief: permanent, root-capable Hephaestus MCP with GPT-5.6-Sol

Use case: infographic-diagram
Asset type: engineering review diagram for a brownfield MCP deployment
Primary request: Draw a precise left-to-right architecture showing how an external MCP host reaches a root-capable Codex worker on one Linux server after this change.

The leftmost zone is “External MCP client”. Show three required connection facts together: Streamable HTTP, `https://heph.kijko.nl/mcp`, and `Authorization: Bearer …`. Put a lock icon on the bearer boundary and make clear that unauthenticated traffic stops with 401.

The middle ingress zone is Cloudflare. Show stable DNS `heph.kijko.nl` entering a named tunnel with a durable tunnel ID, then forwarding to loopback `127.0.0.1:8765`. Visually cross out a small grey rotating `*.trycloudflare.com` quick-tunnel path as legacy and out of the active route.

The server zone contains the existing FastMCP application. Inside it, show four successive gates: bearer middleware; model/effort validation; path guard configured by an explicit full-server deployment flag; SessionManager. Annotate the model gate with default `gpt-5.6-sol` and the six exact supported efforts `low · medium · high · xhigh · max · ultra`. Add a smaller compatibility branch for `gpt-5.5` and `gpt-5.4`, each limited to `low · medium · high · xhigh`.

From SessionManager, show a subprocess arrow to the existing Hephaestus wrapper and then Codex CLI. Mark the actual launch contract: selected model and effort become environment/config arguments; dangerous sandbox mode is explicit. End at a Linux filesystem/server box labelled `/` with a harmless `sudo -n id -u → 0` verification badge, indicating root-capable hands-on access.

Off to the lower side, show Google Drive `KEYMAKER.env` as the canonical client-config record. It receives a readback-verified update containing the permanent URL, model, effort set, and root-equivalent warning, while the existing bearer value is preserved. Connect it to the external client setup, not to the server’s runtime authentication source. Separately show the server token source as the 0600 local file `~/.hephaestus-mcp/api-key.txt`.

Visual vocabulary: blue for unchanged existing components, amber for modified configuration/validation, green for live verified behavior, red for the root-equivalent security boundary, dashed grey for rejected legacy quick tunnel. Use monospace labels for URLs, paths, model slugs, env flags, and commands. Keep all text legible and spell technical strings exactly.

INVARIANTS THE PICTURE MUST ENCODE:
- Bearer auth remains mandatory before any tool or root-capable action.
- The named tunnel is ingress only; it does not store the API key.
- `KEYMAKER.env` is a client secret/config record, not the runtime token source.
- Safe application defaults are not globally weakened; full server access comes from an explicit deployment flag.
- GPT-5.6-Sol has exactly six efforts: low, medium, high, xhigh, max, ultra.
- Legacy models remain but do not receive max or ultra.
- The active code path ends in the existing Hephaestus/Codex subprocess, not a new execution engine.

WHAT THE PICTURE MUST NOT IMPLY:
- Do not show a public unauthenticated route to tools or the filesystem.
- Do not imply Cloudflare Access, mTLS, or a new OAuth provider was added.
- Do not imply the bearer token was rotated or copied into git/tunnel YAML.
- Do not show a Docker container; this service is host-native systemd.
- Do not imply the separate tijmen service or port 8768 was changed.
- Do not present the quick-tunnel hostname as active.

Style/medium: clean professional systems-architecture infographic, high information density but uncluttered, landscape 16:9, flat vector-like shapes, white background, crisp arrows, no decorative people, no watermark.
