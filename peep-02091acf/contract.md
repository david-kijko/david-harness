SEMI-FORMAL BROWNFIELD CONSTRUCTION CERTIFICATE

DEFINITIONS
D1: SUFFICIENT iff every Rn has at least one mapped change in CHANGE SURFACE AND at least one demonstrating NTn in NEW TEST OBLIGATIONS.
D2: MINIMAL iff every row in CHANGE SURFACE cites at least one Rn.
D3: COMPATIBLE iff existing callers are preserved and PASS_TO_PASS tests remain green.
D4: VERIFIABLE iff every Rn maps to a concrete command or observation.

SPEC (verbatim from the user — do not paraphrase)
ticket=KIJ-775 parent=27481ae4-cli-epic

# Implement slice CLI-03 in worktree /home/david/Projects/aiverkeer-cli-impl-cli (branch stream-cli)

Your branch already contains all merged dependency slices — build on what is there; do not re-implement completed dependencies.

# CLI-03 — auth register|login|logout|status  (ticket: KIJ-775)

## Objective
The credential lifecycle in the terminal: register/login exchange the short-lived
session cookie for a PAT (cookie in memory only, discarded after issuance), logout
deletes locally and optionally self-revokes, status renders identity + capabilities.

## Salvage source
`upstream/auth.py@ba1c03c` (register/login semantics, Terms enforcement).

## Research grounding
- Spec §8.6 flows; §11.1 full command contracts (flags, examples, exit codes);
  Terms/Privacy URLs from the consent component.

## Scope (keep–strip–build)
- **Keep**: product's password identity (no invented device flow in v1).
- **Strip**: password via argv/env (never); browser /api/auth/logout call (cookie never
  persisted, nothing to log out).
- **Build**: register (prompt ×2, --accept-terms explicit), login (--token-stdin import
  mode + password mode), logout (--revoke → DELETE /api/tokens/current; partial = exit
  9), status (me + capabilities render).

## Deterministic rules
- Cookie lives only in process memory during exchange; PAT printed never by default.
- --password-stdin warns; CI should use AIVERKEER_API_KEY.
- 409 email-in-use maps to exit 6.

## Tests
QA-02 golden: full lifecycle vs dev; token import of bad/expired/revoked tokens →
exit 3 with the right code; terms not accepted → 400/exit 2.

## Done-when
A fresh machine can register → status → logout --revoke with only the CLI.

## Landing
Branch `david/kij-775-…` off `dev`; PR into `dev`. Depends: CLI-02, BE-03, BE-04.

## Handoff evidence required
Literal terminal transcript of register→status→logout --revoke against dev.

## House rules (every lane)
- Do the work yourself. Do NOT spawn sub-agents. Do NOT end your turn while any step is outstanding.
- Work ONLY in the worktree directory given below. Commit your work on the CURRENT branch with message "<KEY>: <summary>". Do NOT push. Do NOT switch branches.
- Reference material (read, never modify): /home/david/Projects/aiverkeer-cli-shared/
  - SPEC.md — the full aiverkeer CLI specification (section numbers cited in your contract)
  - slices/ — all slice contracts; upstream/ — source snapshots @ ba1c03c
- Environment constraints: Docker is NOT available. Backend tests: pytest + FastAPI TestClient + SQLite (in-memory or file) — add a test fixture that creates the schema; do not require Postgres. Network IS available (pip/npm installs OK).
- Scope discipline: implement YOUR slice only. If your contract references in-flight Linear work (KIJ-743..757) that is absent from this branch, IMPLEMENT the needed subset yourself per the repo plan `Plans/scheduled/crawler-detection-edge-implementation.md` and note it in the commit body.
- Where a done-when requires external infrastructure you cannot reach (Netlify deploys, GitHub secrets, npm publish, Stripe live), implement everything local-executable (files, workflows, dry-runs, tests) and write the gap explicitly into FINALIZE — do not fake it.

## FINALIZE (mandatory, literal — prose claims don't count)
Print at the end:
1. `git log --oneline -3` and `git show --stat HEAD | head -40`
2. Full test-runner output for the tests your contract lists (or the documented gap)
3. A line `LANE-RESULT: <KEY> DONE` or `LANE-RESULT: <KEY> PARTIAL — <one-line reason>`

SPEC DECOMPOSITION (atomic, testable)
R1: Add `auth register` with TTY email fallback, two hidden password prompts, explicit `--accept-terms`, token name/expiry/scope flags, and the documented legal URLs.
R2: Never accept a password through argv or environment; `--password-stdin` is the only headless password path and warns that CI should use `AIVERKEER_API_KEY`.
R3: Register and password login call auth, retain only the returned session cookie in process memory for `POST /api/tokens`, discard it after issuance, validate the PAT through `/api/me`, store it only in the OS credential store, and never print the raw PAT by default.
R4: Add password login and `--token-stdin` import; imports validate `/api/me` plus capabilities before optional storage, and invalid/expired/revoked tokens preserve their stable code with exit 3.
R5: Add local logout for the selected profile plus confirmed `--all-profiles`; never call browser `/api/auth/logout`.
R6: `logout --revoke` calls `DELETE /api/tokens/current` before local deletion, and a failed remote revoke followed by successful local deletion returns exit 9 and warns the server token may remain active.
R7: Add status using `/api/me` and `/api/me/capabilities`, rendering identity, plan state, limits, feature availability, profile, and API URL in human and JSON modes.
R8: Match all CLI-03 flag/help contracts, use inherited global flags, enforce noninteractive prompt safety, and use the existing output envelope/error renderer.
R9: Preserve stable API error mapping, including email-in-use 409 to exit 6, terms 400/422 to exit 2, and credential-store failures to exit 12.
R10: Add executable tests for the complete lifecycle, cookie/PAT non-disclosure, token-state failures, terms rejection, prompt rules, local/all-profile deletion, partial revoke, status rendering, and packed command help.
R11: Produce a literal register→status→logout --revoke transcript against dev; if external dev lacks merged dependency endpoints, record the literal HTTP/CLI gap rather than fabricate success.
R12: Work only in the supplied worktree/current branch, do not push or switch, commit with a `KIJ-775:` subject, and emit the required FINALIZE commands/output.

EXISTING PATTERN SURVEY
| Concern | Hypothesis: pattern exists? | Evidence (file:line) | Still preferred? | Decision |
|---|---|---|---|---|
| Config/profile resolution | yes | cli/src/lib/config.ts:349-412 | yes | REUSE; command flags/env/profile/default precedence already exists. |
| OS credential storage | yes, exact-target only | cli/src/lib/credentials.ts:39-97 | yes but incomplete for all profiles | EXTEND with service-scoped enumeration; do not add plaintext fallback. |
| HTTP/version/retry/error parsing | yes | cli/src/lib/http.ts:105-135,137-315 | yes | REUSE through HttpClient; session cookie is passed explicitly for the one issuance call. |
| Stable exit codes | yes | cli/src/lib/errors.ts:1-88 | yes | REUSE; only construct a partial-success error for logout. |
| Human/JSON rendering and redaction | yes | cli/src/lib/output.ts:128-210; cli/src/lib/redaction.ts:1-93 | yes | REUSE; auth commands never put raw PAT/cookie in success data. |
| Noninteractive safety | yes | cli/src/lib/safety.ts:8-49 | yes | EXTEND with auth-specific visible/hidden prompt adapters. |
| Command implementations | no | cli/src/commands/.gitkeep:1 | n/a | NEW four oclif leaf commands. |
| Backend auth/PAT/capabilities | yes | backend/app/routes/auth.py:60-140; backend/app/routes/tokens.py:116-273; backend/app/routes/me.py:44-74 | yes, read-only dependency | REUSE exact request/response contracts; no backend edits. |
| Terms/privacy URLs | yes | frontend/app/_components/consent-checkbox.tsx:29-45; shared SPEC.md:347-358 | yes | REUSE canonical absolute URLs. |

INTEGRATION POINTS
IP1: cli/src/base-command.ts:5-7 — oclif command inheritance — new auth command base retains inherited global flags.
IP2: cli/src/lib/config.ts:349-412 — invocation configuration — every auth command resolves one target/profile.
IP3: cli/src/lib/credentials.ts:50-97 — credential persistence/resolution — exchange/import/logout/status share the canonical adapter.
IP4: cli/src/lib/http.ts:137-315 — API calls — auth service uses the existing client and error mapping.
IP5: backend/app/routes/auth.py:60-140 — session issuance — CLI captures only the response `session` cookie.
IP6: backend/app/routes/tokens.py:116-232,266-273 — PAT create/self-revoke — CLI sends intent/idempotency headers and Bearer self-revoke.
IP7: backend/app/routes/me.py:44-74 — identity/capabilities — import/status validation and rendering.

INVARIANTS THAT MUST BE PRESERVED
INV1: Tokens never enter TOML/plaintext fallback — Evidence: cli/src/lib/config.ts:85-106 and cli/src/lib/credentials.ts:50-97. Preservation: only CredentialStore.set receives a PAT.
INV2: Raw credentials are redacted from diagnostics/errors — Evidence: cli/src/lib/output.ts:148-180 and cli/src/lib/redaction.ts:1-93. Preservation: result types omit raw token and no cookie/token is passed to renderer.
INV3: HTTP status/detail.code mapping remains authoritative — Evidence: cli/src/lib/errors.ts:42-88 and cli/src/lib/http.ts:105-134. Preservation: new API operations do not scrape messages or remap 401/409.
INV4: POST/DELETE do not retry without idempotency — Evidence: cli/src/lib/http.ts:177-181,291-299. Preservation: only PAT issuance opts into the backend Idempotency-Key contract; revoke does not retry.
INV5: CI/non-TTY never prompts — Evidence: cli/src/lib/safety.ts:8-10,42-49. Preservation: auth input collection checks the same interaction state before any prompt.
INV6: Browser cookie flow remains untouched — Evidence: backend/app/routes/auth.py:143-146. Preservation: CLI never calls that endpoint and never persists the session cookie.

CHANGE SURFACE
| File | New / Modified | Approx lines | Discharges Rn |
|---|---|---:|---|
| cli/src/auth-command.ts | New | 90 | R7,R8,R9 |
| cli/src/lib/auth.ts | New | 300 | R3-R7,R9 |
| cli/src/lib/input.ts | New | 150 | R1,R2,R8 |
| cli/src/lib/credentials.ts | Modified | 35 | R5,R9 |
| cli/src/lib/index.ts | Modified | 2 | R3-R9 |
| cli/src/commands/auth/register.ts | New | 130 | R1-R3,R8,R9 |
| cli/src/commands/auth/login.ts | New | 150 | R2-R4,R8,R9 |
| cli/src/commands/auth/logout.ts | New | 90 | R5,R6,R8 |
| cli/src/commands/auth/status.ts | New | 70 | R7,R8 |
| cli/test/unit/auth.test.ts | New | 400 | R3-R7,R9,R10 |
| cli/test/unit/input.test.ts | New | 100 | R1,R2,R8,R10 |
| cli/test/unit/credentials.test.ts | Modified | 45 | R5,R9,R10 |
| cli/test/integration/fixture-server.test.ts | Modified | 220 | R3-R7,R9-R11 |
| cli/test/e2e/packed-binary.test.ts | Modified | 35 | R8,R10 |

REQUIREMENT → CODE MAPPING
R1 → register command + input adapter; spec-decomposition.
R2 → command flag surface intentionally has no password flag and stdin helper emits warning; invariant-preservation.
R3 → AuthService password exchange and result types; new-construction over HttpClient/CredentialStore patterns.
R4 → AuthService token import plus login mode validator; pattern-reuse.
R5 → AuthService logout plus credential enumeration and confirmation; new-construction.
R6 → AuthService revoke-finally-delete ordering and partial CliError; spec-decomposition.
R7 → status method and status command rendering; pattern-reuse of renderObject/OutputRenderer.
R8 → AuthCommand wrapper and four oclif command definitions; pattern-reuse.
R9 → existing ApiError/CredentialStoreError, with no message scraping; invariant-preservation.
R10 → auth/input/credential/integration/e2e tests; spec-decomposition.
R11 → live dev transcript command plus local fixture fallback; spec-decomposition.
R12 → git status/log/show and no-push inspection; operational proof.

BACKWARD-COMPATIBILITY TRACE
Existing callers of changed code:
C1: cli/test/unit/credentials.test.ts:39-128 uses SystemCredentialStore exact target methods. After change: STILL SATISFIED; enumeration is additive.
C2: cli/src/lib/index.ts:1-8 is a public barrel. After change: STILL SATISFIED; exports are additive.
C3: cli/src/base-command.ts:5-7 is checked by cli/test/unit/global-flags.test.ts:22-45. After change: STILL SATISFIED; baseFlags identity is retained.
C4: cli/src/lib/http.ts callers expect Bearer/version/retry semantics. After change: STILL SATISFIED; no HttpClient mutation planned.
Existing PASS_TO_PASS tests: all 53 unit, 2 integration, and packed version/help test from the literal pre-change `npm test` transcript must remain green.

NEW TEST OBLIGATIONS
NT1: register password exchange — request order/body, cookie header only on PAT issuance, final Bearer `/api/me`, credential stored, no raw secret in result/output. Runnable: `npm run test:unit -- --test-name-pattern='register'`.
NT2: token import state table — invalid/expired/revoked each exit 3 with exact code and no store write. Runnable: `npm run test:unit -- --test-name-pattern='token import'`.
NT3: terms rejected — structured and legacy 400 map to exit 2. Runnable: `npm run test:unit -- --test-name-pattern='terms'`.
NT4: password input — two hidden register prompts, mismatch, stdin warning, CI/non-TTY guard. Runnable: `npm run test:unit -- --test-name-pattern='password'`.
NT5: logout — local, all-profile, remote self-revoke ordering, no browser logout, failure+local delete exit 9. Runnable: `npm run test:unit -- --test-name-pattern='logout'`.
NT6: status — exact identity/capabilities data and human rendering. Runnable: `npm run test:unit -- --test-name-pattern='status'`.
NT7: literal local HTTP lifecycle — register→status→logout uses expected methods/paths/headers and no secret transcript. Runnable: `npm run test:integration`.
NT8: packed command discovery/help — root and four leaf helps execute. Runnable: `npm run test:e2e`.
NT9: compatibility — lint/typecheck/build/full suite. Runnable: `npm run lint && npm run typecheck && npm run build && npm test`.
NT10: dev handoff — unique disposable email lifecycle with literal stdout/stderr/exit. Runnable: guarded shell transcript against `https://dev-ai-verkeer-api.procesgroei.nl`; record dependency 404 if unavailable.
NT11: git discipline — current branch is stream-cli, one KIJ-775 commit, no push. Runnable: `git status --short --branch; git log --oneline -3; git show --stat HEAD | head -40`.

COUNTEREXAMPLE / SUFFICIENCY CHECK
R1 → Soundness: missing terms is rejected before password collection; interactive register calls secret prompt twice and compares.
R2 → Soundness: no command flag/environment lookup exists for password; only stdin/prompt return it.
R3 → Soundness: session value is a method-local string used once as a Cookie header; returned data omits PAT and store receives it after validation. Counterexample tested: recognizable PAT/cookie must not appear in transcript.
R4 → Soundness: store write is sequenced after both validation GETs. Counterexamples: each 401 code aborts before write.
R5 → Soundness: exact target deletion reuses canonical account derivation; all-profile enumeration is scoped to service `aiverkeer`. Counterexample: noninteractive all-profile without `--yes` exits 2 without deletion.
R6 → Soundness: local deletion is in a guaranteed post-revoke path; a saved remote error is converted to exit 9 only after local deletion succeeds.
R7 → Soundness: output is constructed from `/api/me` plus capabilities, not a duplicated plan matrix. Counterexample: missing credential exits 3.
R8 → Soundness: all commands subclass the existing BaseCommand and render through OutputRenderer; parser failures are normalized to usage output.
R9 → Soundness: ApiError detail.code remains authoritative and existing mappings already contain all CLI-03 codes.
R10 → Soundness: NT1-NT8 cover every functional partition, including success/error/noninteractive/security paths.
R11 → Counterexample response: dev currently returns 404 for `/api/me/capabilities`; if still stale at handoff, literal output is retained and lane marked PARTIAL rather than claiming dev success.
R12 → Soundness: backup bundle exists; final git commands and commit prove lane state, and remote refs are not changed.
Coverage note: interactive TTY behavior is unit-tested through injected prompt adapters; packed-process lifecycle uses stdin/headless mode. OS-specific keyring implementations remain the dependency adapter's cross-platform obligation, with this Linux host behavior exercised manually.

UI_BEHAVIOR_AFFECTING: no

FORMAL CONCLUSION
By D1 (SUFFICIENT): yes — R1-R12 map to code/operations and NT1-NT11.
By D2 (MINIMAL): yes — every planned file discharges an auth requirement; no backend/frontend production edits.
By D3 (COMPATIBLE): yes, contingent on the full pre-existing suite remaining green after implementation.
By D4 (VERIFIABLE): yes — every requirement has a concrete test or literal operational command.

Plan is READY TO IMPLEMENT: YES
