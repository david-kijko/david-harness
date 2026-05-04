```
SEMI-FORMAL BROWNFIELD CONSTRUCTION CERTIFICATE

DEFINITIONS
D1: SUFFICIENT iff every Rn has at least one mapped change in CHANGE SURFACE
    AND at least one demonstrating NTn in NEW TEST OBLIGATIONS.
D2: MINIMAL iff every row in CHANGE SURFACE cites at least one Rn (no
    over-refinement; no file changed without a requirement attached).
D3: COMPATIBLE iff every existing caller in BACKWARD-COMPATIBILITY TRACE
    is preserved or its breakage is explicitly justified, AND every
    PASS_TO_PASS test on the change surface remains green by trace.
D4: VERIFIABLE iff every Rn maps to at least one NTn whose pass/fail can
    be observed by running a concrete command.

SPEC (verbatim from the user — do not paraphrase)
"Add retry-with-exponential-backoff to BarClient's two methods (`get_gadget`,
`list_gadgets`). The intent is to handle transient 5xx and connection
errors gracefully. Don't add retry to `__init__`."

SPEC DECOMPOSITION (atomic, testable)
R1: BarClient.get_gadget retries on transient failures with exponential
    backoff before raising.
R2: BarClient.list_gadgets retries on transient failures with exponential
    backoff before raising.
R3: Retries trigger on transient HTTP 5xx responses.
    AMBIGUITY: the spec says "5xx and connection errors gracefully" but
    the existing `with_retry` decorator triggers only on caught exceptions.
    BarClient currently uses `resp.raise_for_status()` which raises
    `requests.HTTPError` on 5xx (and 4xx). Two readings:
      R3.a: retry on `requests.HTTPError` (covers 5xx but ALSO 4xx —
            wider than spec).
      R3.b: retry only on 5xx by inspecting status_code, raise 4xx
            immediately (matches spec exactly).
    DECISION: implement R3.b. 4xx are not transient ("gracefully" implies
    transient-only); retrying a 404 wastes the user's time. Mechanism:
    raise a narrow exception type only for 5xx and configure
    `with_retry(on=...)` to that type. 4xx still raises HTTPError on the
    first attempt.
R4: Retries trigger on connection errors (`requests.ConnectionError`,
    `requests.Timeout`).
R5: Retries do NOT trigger on `BarClient.__init__`.
R6: After exhausting attempts, the final underlying exception propagates
    to the caller (no swallowing).

OUT OF SCOPE (explicitly):
- Migrating FooClient off legacy_retry (ticket #4421 covers that).
- Adding retry to non-HTTP methods.
- Configurable per-call retry tuning (no requirement attached).
- Logging/metrics on retry (not requested).

EXISTING PATTERN SURVEY  (mandatory — guards B1, B2)

| Concern | Hypothesis: pattern exists? | Evidence (file:line) | Still preferred? | Decision |
|---|---|---|---|---|
| Generic retry helper | yes | `src/util/retry.py:10` defines `with_retry`, decorator-or-function form, exponential backoff `base_delay * 2**attempt`, jitter, configurable exception filter via `on=` | yes — module docstring at `src/util/retry.py:1-2` says "Canonical retry helper… Replaces src/clients/legacy_retry.py for all new code" | REUSE `with_retry` |
| Legacy retry helper | yes (still imported) | `src/clients/legacy_retry.py:4` defines `retry_legacy`; used by `src/clients/foo.py:1` | NO — `src/clients/legacy_retry.py:1-2` marks it DEPRECATED; ticket #4421 covers full removal | DO NOT use `retry_legacy` for new code (B2 guard) |
| Retry-on-HTTP-status helper | searched both retry modules — none exist | `src/util/retry.py:10` only filters by exception type via `on=`; no status-code-aware variant | n/a | EXTEND by raising a narrow exception subclass for 5xx and passing it as `on=` |
| Convention for HTTP errors in clients | `BarClient` uses `resp.raise_for_status()` | `src/clients/bar.py:9, 14` | yes — keep using raise_for_status semantics where applicable | Preserve raise_for_status semantics for non-5xx |

NEW vs REUSE proof obligations:
- REUSE `with_retry` (not `retry_legacy`): discharged by deprecation
  notice at `src/clients/legacy_retry.py:1-2` and canonical-replacement
  notice at `src/util/retry.py:1-2`. (B2 guard satisfied.)
- NEW small exception class `TransientHTTPError` (subclass of
  `requests.HTTPError`) inside `src/clients/bar.py`: justified because
  `with_retry`'s only filter mechanism is exception-type via `on=`, and
  no existing exception in `requests` distinguishes 5xx from 4xx. The
  class is the minimal adapter that lets us reuse the canonical helper
  without adding a status-code-aware retry variant (which would itself
  be pattern reinvention — B1 guard).

INTEGRATION POINTS  (where new code touches existing code)
IP1: `src/clients/bar.py:1` — add imports for `with_retry` and the
     transient exceptions (`requests.ConnectionError`, `requests.Timeout`).
IP2: `src/clients/bar.py:6-11` (`get_gadget`) — wrap HTTP work; on 5xx,
     raise `TransientHTTPError` so `with_retry` catches it.
IP3: `src/clients/bar.py:13-16` (`list_gadgets`) — same wrapping pattern
     as IP2.
IP4: `src/clients/bar.py:4-5` (`__init__`) — UNCHANGED (R5).
IP5: `tests/clients/test_bar_client.py:5-9` — existing test patches
     `src.clients.bar.requests.get`. Patch target stays valid because we
     keep importing `requests` at module top. Existing assertion (one
     successful call returns json) must still hold (PASS_TO_PASS).

INVARIANTS THAT MUST BE PRESERVED  (guards B3)
INV1: BarClient methods return parsed JSON on success.
      Evidence: `src/clients/bar.py:11, 16` (`return resp.json()`); test
      `tests/clients/test_bar_client.py:9` asserts `result == {"id": "g1"}`.
      Why preserved: wrapping the body in `with_retry` does not alter
      the return value; on success the wrapper simply returns whatever
      the wrapped function returned (`src/util/retry.py:19`).
INV2: 4xx errors surface to the caller (not silently retried away).
      Evidence: `src/clients/bar.py:9, 14` use `resp.raise_for_status()`,
      which raises `requests.HTTPError` for any 4xx/5xx.
      Why preserved: we narrow the retried exception to a 5xx-only
      subclass `TransientHTTPError`. 4xx still hits `raise_for_status`
      and propagates out of the wrapped call as plain `requests.HTTPError`,
      which is NOT in `with_retry(on=...)`, so it propagates immediately
      (`src/util/retry.py:18-20` — only `except on` is caught).
INV3: The patch target `src.clients.bar.requests.get` remains valid.
      Evidence: `tests/clients/test_bar_client.py:6`.
      Why preserved: we keep `import requests` at the top of `bar.py`.
INV4: `with_retry`'s decorator semantics: it re-raises the LAST exception
      after `max_attempts` (`src/util/retry.py:21-22`).
      Why this matters: R6 (final exception propagates) is satisfied
      "for free" by the helper.
INV5: BarClient construction performs no I/O (no network call in
      `__init__`).
      Evidence: `src/clients/bar.py:4-5`.
      Why preserved: R5 + change does not touch `__init__`.

CHANGE SURFACE  (every file that changes — guards B4 via D2)

| File | New / Modified | Approx lines | Discharges Rn |
|---|---|---|---|
| `src/clients/bar.py` | Modified | +~20 / -~6 (add imports, add `TransientHTTPError`, add `_request_json` private helper decorated with `with_retry`, rewrite `get_gadget` and `list_gadgets` to call the helper) | R1, R2, R3 (via R3.b), R4, R5, R6 |
| `tests/clients/test_bar_client.py` | Modified | +~60 (new tests for retry-on-5xx, retry-on-ConnectionError, no-retry-on-4xx, exhaustion-reraises, init-does-not-retry); also patch `src.clients.bar.time.sleep` to keep tests fast | R1, R2, R3, R4, R5, R6 |

(No other files changed. `legacy_retry.py` and `foo.py` are NOT touched —
that's ticket #4421's scope, not ours. `util/retry.py` is NOT changed —
its API already supports what we need.)

REQUIREMENT → CODE MAPPING  (guards B5 via D1)
R1 → satisfied by `src/clients/bar.py` `get_gadget` calling
     `self._request_json(url)` where `_request_json` is decorated with
     `@with_retry(on=(TransientHTTPError, requests.ConnectionError, requests.Timeout))`;
     trace: caller -> wrapper loop in `src/util/retry.py:17-26` ->
     `_request_json` -> `requests.get` -> `raise_for_status` (or
     `TransientHTTPError` if 5xx) -> exception caught -> backoff ->
     retry. Inference type: pattern-reuse.
R2 → satisfied by `src/clients/bar.py` `list_gadgets` calling the same
     `_request_json(url)` helper; identical trace as R1. Inference type:
     pattern-reuse.
R3 (= R3.b) → satisfied inside `_request_json`: after `requests.get`,
     check `if 500 <= resp.status_code < 600: raise TransientHTTPError(...)`;
     `TransientHTTPError` is in `with_retry(on=...)`, so it triggers
     retry. 4xx is handled by `resp.raise_for_status()` raising plain
     `requests.HTTPError`, which is NOT in `on=...` and so propagates
     immediately. Inference type: new-construction (the narrow
     exception class) + invariant-preservation (raise_for_status).
R4 → satisfied because `requests.ConnectionError` and `requests.Timeout`
     are raised by `requests.get` itself before any response object
     exists (`requests` library contract — ASSUMPTION: standard
     `requests` semantics, source not verified in this slice). They are
     listed in `with_retry(on=...)`, so the wrapper catches and retries.
     Inference type: pattern-reuse.
R5 → satisfied because `__init__` is not modified and contains no
     retry-eligible call (`src/clients/bar.py:4-5` only assigns
     `self.base_url`). Inference type: invariant-preservation (INV5).
R6 → satisfied by `with_retry`'s final-attempt branch
     (`src/util/retry.py:21-22`: `if attempt == max_attempts - 1: raise`)
     which re-raises the original caught exception. Inference type:
     pattern-reuse.

BACKWARD-COMPATIBILITY TRACE  (guards B6, B7 via D3)
Existing callers of changed code:
  C1: No in-tree caller of `BarClient.get_gadget` or `BarClient.list_gadgets`
      appears in the provided slice. Public API shape (method name,
      arity, return type) is unchanged: STILL SATISFIED.
  C2: Test file `tests/clients/test_bar_client.py:5-9` calls
      `BarClient("https://api.example.com").get_gadget("g1")` and
      expects `{"id": "g1"}`. After change: STILL SATISFIED — on the
      mocked happy path (status 200 implied because `raise_for_status`
      is mocked to a no-op MagicMock and the 5xx check uses
      `resp.status_code` which on a `MagicMock` returns a MagicMock).
      RISK: the new 5xx check `500 <= resp.status_code < 600` will fail
      on a `MagicMock` because comparison of MagicMock to int raises
      `TypeError` in Python 3.
      MITIGATION: update the existing test to set
      `mock_get.return_value.status_code = 200` so the comparison is
      well-defined. This is a TEST-ONLY update reflecting the new
      contract, not a breakage of the production API.

Existing tests touching the change surface (PASS_TO_PASS):
  T1: `tests/clients/test_bar_client.py::test_get_gadget_returns_json`
      — MUST UPDATE: add `mock_get.return_value.status_code = 200` to
      keep the test green under the new 5xx check. The assertion
      (`result == {"id": "g1"}`) is unchanged. This is the minimum
      diff required to preserve the original intent of the test.

NEW TEST OBLIGATIONS  (guards D4)
All new tests patch both `src.clients.bar.requests.get` and
`src.clients.bar.time.sleep` (the latter via `with_retry`'s `time` import
— actually `with_retry` imports `time` in `src/util/retry.py:2`, so the
correct patch target is `src.util.retry.time.sleep`). Tests also pass
`max_attempts=3` implicitly (the default).

NT1: `test_get_gadget_retries_on_5xx_then_succeeds` — Demonstrates R1+R3.
     Mock `requests.get` to return status_code=503 twice, then 200 with
     `{"id":"g1"}`. Assert call count == 3 and result == {"id":"g1"}.
     Runnable: `pytest tests/clients/test_bar_client.py::test_get_gadget_retries_on_5xx_then_succeeds`

NT2: `test_list_gadgets_retries_on_5xx_then_succeeds` — Demonstrates R2+R3.
     Same shape as NT1 but for `list_gadgets`.
     Runnable: `pytest tests/clients/test_bar_client.py::test_list_gadgets_retries_on_5xx_then_succeeds`

NT3: `test_get_gadget_retries_on_connection_error_then_succeeds` —
     Demonstrates R4. Mock `requests.get` to raise
     `requests.ConnectionError` twice, then return a 200 JSON. Assert
     call count == 3.
     Runnable: `pytest tests/clients/test_bar_client.py::test_get_gadget_retries_on_connection_error_then_succeeds`

NT4: `test_get_gadget_does_not_retry_on_4xx` — Demonstrates R3 boundary
     (4xx is not transient). Mock `requests.get` to return status_code=404
     with `raise_for_status` raising `requests.HTTPError`. Assert
     `pytest.raises(requests.HTTPError)` and call count == 1.
     Runnable: `pytest tests/clients/test_bar_client.py::test_get_gadget_does_not_retry_on_4xx`

NT5: `test_get_gadget_reraises_after_exhaustion` — Demonstrates R6.
     Mock `requests.get` to return status_code=500 every time. Assert
     `pytest.raises(TransientHTTPError)` and call count == 3 (default
     `max_attempts`).
     Runnable: `pytest tests/clients/test_bar_client.py::test_get_gadget_reraises_after_exhaustion`

NT6: `test_init_does_no_io_and_does_not_retry` — Demonstrates R5. Mock
     `requests.get` and assert that `BarClient("...")` constructor does
     NOT call it (call count == 0) and does not sleep.
     Runnable: `pytest tests/clients/test_bar_client.py::test_init_does_no_io_and_does_not_retry`

NT7 (regression-hardening): keep the updated T1 in the suite as
     `test_get_gadget_returns_json` (single successful call, count == 1,
     no sleeps).

COUNTEREXAMPLE / SUFFICIENCY CHECK  (per-Rn binary)

R1 → (a) Soundness sketch: P(input) = "for a transient sequence of
     responses ending in success, get_gadget eventually returns the
     parsed JSON of the success response, within `max_attempts` tries."
     `_request_json` is `with_retry`-decorated, so the wrapper loop
     (`src/util/retry.py:17-26`) iterates up to `max_attempts`; on
     non-final transient exceptions, it sleeps and retries; on success
     it returns immediately (`src/util/retry.py:19`). Therefore P holds
     for any transient prefix of length < `max_attempts`. ∎

R2 → (a) Same argument as R1, applied to `list_gadgets`, which routes
     through the same `_request_json` helper. ∎

R3 → (a) Soundness sketch for the 5xx branch: P(input) = "if the server
     returns 5xx, retry; if 4xx, do not retry." 5xx path: explicit check
     `if 500 <= resp.status_code < 600: raise TransientHTTPError(...)`,
     and `TransientHTTPError ∈ on=...`, so caught and retried. 4xx path:
     `resp.raise_for_status()` raises `requests.HTTPError`, which is NOT
     in `on=...`; per `src/util/retry.py:18-20` only `except on` is
     caught, so the exception escapes the wrapper on the first attempt. ∎
     COUNTEREXAMPLE PROBE: status 200 with malformed JSON — `resp.json()`
     raises `ValueError`/`JSONDecodeError`, which is not in `on=...`,
     so it propagates. INTENDED — corrupt payload is not "transient"
     in the stated spec.
     COUNTEREXAMPLE PROBE: status 5xx but `raise_for_status` order — we
     check status_code BEFORE calling raise_for_status, so 5xx becomes
     `TransientHTTPError` (retried) rather than `HTTPError` (not
     retried). Order is load-bearing — flag for the implementer.

R4 → (a) `requests.ConnectionError` and `requests.Timeout` are raised
     by `requests.get` before any response is returned (ASSUMPTION,
     standard `requests` library behavior — flagged, not verified
     in-slice). Both are listed in `on=...`, so the wrapper catches
     them. ∎

R5 → (a) `__init__` is not on the change surface (`src/clients/bar.py:4-5`
     remains the assignment of `self.base_url`). NT6 mechanically
     verifies no I/O happens at construction. ∎

R6 → (a) `with_retry` final-attempt branch (`src/util/retry.py:21-22`)
     re-raises the caught exception. NT5 verifies this concretely. ∎

Coverage check: NT1+NT2 exercise 5xx-then-success on both methods (R1, R2,
R3). NT3 exercises ConnectionError (R4). NT4 exercises the 4xx no-retry
boundary (R3 negative case). NT5 exercises exhaustion (R6 + R3). NT6
exercises init-no-retry (R5). Updated T1 keeps the original happy-path
regression. Unexercised partition: `requests.Timeout` specifically (only
ConnectionError is tested in NT3). Acceptable: both go through the same
`on=...` tuple by the same mechanism, so NT3 is a representative for
the connection-error class. If desired, parameterize NT3 over both.

FORMAL CONCLUSION
By D1 (SUFFICIENT): YES — every Rn (R1..R6) has a CHANGE SURFACE entry
   AND at least one NT (R1→NT1, R2→NT2, R3→NT1+NT4+NT5, R4→NT3, R5→NT6,
   R6→NT5).
By D2 (MINIMAL): YES — both rows in CHANGE SURFACE cite Rns; no other
   files are touched. Specifically `src/clients/legacy_retry.py`,
   `src/clients/foo.py`, and `src/util/retry.py` are NOT modified.
By D3 (COMPATIBLE): YES — only one existing caller-equivalent (T1) is
   affected; it requires a one-line additive update
   (`status_code = 200`) that preserves its original assertion. No
   production caller in the slice changes shape.
By D4 (VERIFIABLE): YES — every Rn maps to at least one runnable
   pytest invocation listed under NEW TEST OBLIGATIONS.

Plan is READY TO IMPLEMENT: YES.
```

---

## Implementer-facing summary (concrete code shape)

`src/clients/bar.py` (post-change shape, for the implementer):

```python
import requests
from src.util.retry import with_retry


class TransientHTTPError(requests.HTTPError):
    """5xx response — eligible for retry. 4xx is NOT this type."""


_TRANSIENT = (TransientHTTPError, requests.ConnectionError, requests.Timeout)


class BarClient:
    def __init__(self, base_url):
        self.base_url = base_url  # unchanged — R5

    @with_retry(on=_TRANSIENT)
    def _request_json(self, url):
        resp = requests.get(url)
        if 500 <= resp.status_code < 600:
            raise TransientHTTPError(
                f"{resp.status_code} server error", response=resp
            )
        resp.raise_for_status()  # 4xx propagates as plain HTTPError
        return resp.json()

    def get_gadget(self, gadget_id):
        return self._request_json(f"{self.base_url}/gadgets/{gadget_id}")

    def list_gadgets(self):
        return self._request_json(f"{self.base_url}/gadgets/")
```

Notes for the implementer:
- The 5xx check MUST run before `raise_for_status()` (order is load-bearing — see R3 counterexample probe).
- The decorator uses `with_retry`'s defaults (`max_attempts=3`, `base_delay=0.5`, `jitter=True`). Spec did not request configurability; do not add it (B4 guard).
- Tests should patch `src.util.retry.time.sleep` (not `src.clients.bar.time.sleep`) because `time` is imported inside `src/util/retry.py:2`, not in `bar.py`. Without this, the test suite will sleep ~1.5s per retry test.
- Do NOT touch `legacy_retry.py` or `foo.py` — ticket #4421 owns that migration.
