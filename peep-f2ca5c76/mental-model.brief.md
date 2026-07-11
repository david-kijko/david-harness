# BE-08 mental model

Create a clean backend security architecture diagram, not a UI mockup. Show an existing session-authenticated user at the left requesting a PAT from the existing `/api/tokens` path. The token issuer consults the newly persisted `users.is_admin` boolean: ordinary scopes flow normally, while `admin:read` and `admin:write` are blocked with 403 unless the boolean is true. Explicitly show that email address, hostname, and request origin do not feed the role decision.

On the right, show a future `/api/admin/*` endpoint using `Depends(require_admin("admin:read" or "admin:write"))`. The incoming credential must be a Bearer PAT. Draw two sequential gates: the existing PAT scope validator, then a fresh database lookup of the token owner's `is_admin` value. Both gates must be green before the endpoint runs. Include the adversarial case of an admin-scoped token row owned by a non-admin: it passes scope but stops at the role gate.

Below that path, show one append-only flow into `admin_audit_log`. The row contains a non-secret principal label, actor user ID, actor token-row ID, route action, path-parameter target, allowlisted method/route metadata, sanitized result, request ID, and timestamp. Do not depict raw PAT text, cookies, authorization headers, request bodies, edge keys, provider secrets, query values, or user-agent values entering the audit table. Represent the table as write-once: INSERT enters; UPDATE and DELETE hit hard database barriers. Note that PostgreSQL additionally revokes UPDATE/DELETE from PUBLIC.

Separate a small manual provisioning lane: a named database operator and change ticket execute one transaction keyed by immutable user ID that changes `is_admin` and inserts a grant/revoke audit row. Make clear there is no CLI `make admin`, no email pattern, and no hostname shortcut.

Visual vocabulary: existing components in muted blue, newly added BE-08 components in amber, preserved customer paths in green, denied flows in red, and append-only invariants as lock symbols. Enclose only `models.py`, `admin.py`, `security.py`, `routes/tokens.py`, migration 011, focused tests, and the provisioning runbook inside the BE-08 change boundary. Keep BE-09 health/jobs and CLI-10 outside the boundary as grey future consumers.

Invariants the picture must encode: role and admin scope are both mandatory; the role is checked again on every admin request; default users are non-admin; exactly one request-audit insert occurs for the demonstrated successful call; audit mutation is blocked; secret credential material never reaches audit storage; customer-facing routes keep their current behavior.

The picture must not imply that sessions satisfy admin scope, that an email domain grants a role, that the audit record can be updated with a later result, that BE-09 endpoints are implemented here, that the CLI can provision admins, or that unrelated crawler/edge/customer code changes.
