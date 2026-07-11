SEMI-FORMAL BROWNFIELD CONSTRUCTION CERTIFICATE

DEFINITIONS
D1: SUFFICIENT iff every Rn has at least one mapped change in CHANGE SURFACE and at least one demonstrating NTn.
D2: MINIMAL iff every CHANGE SURFACE row cites at least one Rn.
D3: COMPATIBLE iff existing callers are preserved and PASS_TO_PASS coverage remains green.
D4: VERIFIABLE iff every Rn has a concrete runnable observation.

SPEC
The byte-exact task text is stored in spec.txt beside this certificate.

SPEC DECOMPOSITION
R1: Persist `User.is_admin` as non-null false-by-default through Alembic, with no email or host inference.
R2: Reject non-admin session users requesting either admin PAT scope with HTTP 403 and code `admin_scope_forbidden`; allow admins.
R3: Provide `require_admin(scope)` so an admin PAT must have the requested admin scope and its current owning user must still have `is_admin=true`.
R4: Persist one sanitized audit row for each request that reaches the admin dependency, with principal, actor IDs, action, target, metadata, result, request ID, and time.
R5: Make audit records append-only: application code has only an insert helper and supported databases reject UPDATE/DELETE; PostgreSQL also revokes those grants from PUBLIC.
R6: Document a manual, ticketed, atomic, audited grant/revoke runbook keyed by immutable user ID.
R7: Preserve customer-facing behavior and dependency slices; use SQLite/FastAPI TestClient and commit only the current branch without switching.
R8: Produce literal 403 and audit SELECT evidence plus required test and git finalize output.
OUT OF SCOPE: BE-09 health/jobs endpoints, CLI-10 commands, email-based roles, a CLI admin-provisioning command, and unrelated dependency work.

EXISTING PATTERN SURVEY
| Concern | Hypothesis | Evidence | Still preferred? | Decision |
|---|---|---|---|---|
| User persistence | SQLAlchemy declarative model and linear Alembic chain exist | `backend/app/models.py:34-72`; `backend/migrations/versions/010_edge_key_rotation.py:12-15` | yes | EXTEND User and add revision 011. |
| PAT scope catalogue | Admin scopes and non-admin subset already exist | `backend/app/api_tokens.py:15-35` | yes | REUSE; do not redefine scopes. |
| PAT issuance | BE-03 already contains a provisional role check | `backend/app/routes/tokens.py:140-156` | yes after real column exists | EXTEND only by replacing fallback attribute access with explicit role access. |
| Bearer scope enforcement | `_authenticate_bearer` checks required scopes and current token state | `backend/app/security.py:115-174` | yes | REUSE through `Security(get_current_api_token, scopes=[scope])`. |
| Request correlation | Middleware provides and echoes `request.state.request_id` | `backend/app/main.py:123-133` | yes | REUSE; audit never reads secret-bearing headers. |
| Test DB | File SQLite fixture creates all ORM schema and overrides `get_db` | `backend/tests/conftest.py:65-112` | yes | REUSE and add focused BE-08 tests. |
| Admin/audit implementation | Search found no existing admin router, dependency, or audit model | searched `backend/app`, `backend/tests`, migrations for `require_admin` and `admin_audit_log`; no matches | n/a | NEW, confined to one module/model/migration. |

INTEGRATION POINTS
IP1: `backend/app/models.py:34-72` — User schema gains explicit role; new audit model joins Base metadata.
IP2: `backend/app/routes/tokens.py:116-156` — session-only PAT creation reads explicit `user.is_admin`.
IP3: `backend/app/security.py:191-197` — token dependency receives nested Security scopes while existing unscoped revoke caller remains valid.
IP4: `backend/app/main.py:123-133` — existing request ID is read by the dependency, not modified.
IP5: `backend/tests/conftest.py:65-112` — SQLite schema/client fixtures exercise real dependency behavior.

INVARIANTS THAT MUST BE PRESERVED
INV1: Browser session routes continue accepting cookie principals while PAT routes enforce scopes — evidence `backend/app/security.py:177-188`; preserved because only `get_current_api_token` receives SecurityScopes and existing callers pass an empty set.
INV2: Interactive default PAT scopes remain non-admin — evidence `backend/app/routes/tokens.py:35-40`; preserved unchanged.
INV3: Raw PATs are never persisted — evidence hashing/persistence path `backend/app/routes/tokens.py:182-193`; audit records only token row IDs.
INV4: Customer APIs remain untouched — evidence current router mount surface `backend/app/main.py:149-162`; no production admin endpoint is added in BE-08.
INV5: Request IDs remain generated/echoed centrally — evidence `backend/app/main.py:123-133`; dependency only reads the state value.

CHANGE SURFACE
| File | New / Modified | Approx lines | Discharges |
|---|---|---:|---|
| `backend/app/models.py` | Modified | 35 | R1,R4,R5 |
| `backend/app/security.py` | Modified | 4 | R3,R7 |
| `backend/app/routes/tokens.py` | Modified | 2 | R2 |
| `backend/app/admin.py` | New | 130 | R3,R4,R5 |
| `backend/migrations/versions/011_admin_audit.py` | New | 145 | R1,R4,R5 |
| `backend/tests/test_admin.py` | New | 260 | R1-R5,R7,R8 |
| `backend/docs/admin-provisioning.md` | New | 120 | R1,R5,R6 |

REQUIREMENT -> CODE MAPPING
R1 -> model plus revision 011; new-construction grounded in existing migration style.
R2 -> explicit branch in `routes/tokens.py` plus TestClient issuance test; pattern-reuse.
R3 -> `app/admin.py:require_admin` nested Security dependency and request-time user reload; new-construction reusing existing bearer authentication.
R4 -> `append_admin_audit` and dependency finalizer; new-construction with allowlisted metadata only.
R5 -> insert-only helper, grep-level assertion, SQLite/PostgreSQL mutation-rejection triggers, and PostgreSQL REVOKE; invariant-preservation.
R6 -> provisioning runbook with one transaction that changes role and inserts the audit event; spec-decomposition.
R7 -> focused file list and full backend regression suite; invariant-preservation.
R8 -> executable TestClient/SQLite evidence script after implementation; spec-decomposition.

BACKWARD-COMPATIBILITY TRACE
C1: `backend/app/routes/tokens.py:266-273` uses `Depends(get_current_api_token)` with no scopes. After change it receives an empty SecurityScopes list and is STILL SATISFIED.
C2: `backend/app/security.py:177-188` calls `_authenticate_bearer` for bearer customer routes. It is unchanged and STILL SATISFIED.
C3: all User constructors omit `is_admin`; model/Persisted server defaults make them non-admin and STILL SATISFIED (`backend/app/routes/auth.py:85-88`).
T1: `backend/tests/test_tokens.py:64-151` PAT lifecycle remains green because non-admin scopes are unchanged.
T2: `backend/tests/test_auth_principal.py:183-289` scope matrix remains green because SecurityScopes behavior is preserved.
T3: `backend/tests/test_migrations.py:27-33` metadata parity must stay green after revision 011.

NEW TEST OBLIGATIONS
NT1: non-admin admin-scope issuance returns exact 403/code; `pytest -q tests/test_admin.py::test_non_admin_cannot_issue_admin_scopes`.
NT2: admin issuance succeeds and defaults remain non-admin; same test module.
NT3: scoped admin request writes exactly one sanitized row; `pytest -q tests/test_admin.py::test_admin_call_writes_exactly_one_audit_row`.
NT4: a token row manually bearing admin scope for a now/non-admin owner fails request-time role recheck; focused test.
NT5: wrong-scope admin PAT fails; focused test.
NT6: migration has false default and existing-user backfill; focused migrated-database test.
NT7: application-source grep finds no audit mutation call and direct migrated SQLite UPDATE/DELETE both fail; focused append-only test.
NT8: all backend tests run with `pytest -q`.

COUNTEREXAMPLE / SUFFICIENCY CHECK
R1 -> Soundness: omitted role on new/existing users resolves to false through Python and server defaults; migration test covers pre-011 row.
R2 -> Soundness: any requested set containing an admin scope is not a subset of NON_ADMIN scopes; false `is_admin` deterministically raises 403 before token insertion.
R3 -> Counterexample addressed: manually insert an admin-scoped PAT, then set its owner non-admin; token scope passes but role reload rejects.
R4 -> Soundness: one generator dependency has exactly one append on success or route exception, while role denial has one pre-raise append; tests count rows.
R5 -> Counterexample addressed: raw SQL UPDATE/DELETE bypasses ORM, so migration triggers reject both and PostgreSQL PUBLIC grants are revoked.
R6 -> Soundness: transaction couples the immutable role transition audit insert with the update; rollback prevents an unaudited partial transition.
R7 -> Soundness: no customer router/model response shape changes; full suite covers regressions.
R8 -> Soundness: literal TestClient JSON and SQLite SELECT are printed after the commit.
Coverage partitions: non-admin issuance, admin issuance, missing scope, forged/direct admin scope on non-admin, authorized success, route failure, existing migration row, raw update, raw delete. Invalid/unparseable bearer audit is outside the actor-attributable row guarantee because no principal can be established.

UI_BEHAVIOR_AFFECTING: no

FORMAL CONCLUSION
By D1 (SUFFICIENT): yes — each Rn has mapped code and runnable evidence.
By D2 (MINIMAL): yes — every changed file discharges a listed requirement.
By D3 (COMPATIBLE): yes provisionally — existing callers are traced; targeted and full tests must confirm.
By D4 (VERIFIABLE): yes — every requirement has a concrete TestClient, migration, grep, SQL, or documentation observation.

Plan is READY TO IMPLEMENT: YES
