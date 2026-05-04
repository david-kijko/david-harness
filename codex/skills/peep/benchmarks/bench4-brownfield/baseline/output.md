# Plan: Add retry-with-exponential-backoff to `BarClient`

## 1. Which retry helper to reuse — and why

Reuse **`src/util/retry.py::with_retry`**. Reasons traced to the codebase slice:

- `src/util/retry.py` is documented as the "Canonical retry helper" and explicitly says it "Replaces `src/clients/legacy_retry.py` for all new code." `BarClient` getting retry is new code, so it falls squarely under that directive.
- `src/clients/legacy_retry.py` carries a `DEPRECATED` notice. Ticket #4421 tracks its removal once `src/clients/foo.py` migrates. Adding a second consumer of `retry_legacy` would actively make that ticket harder to close (one more migration, not zero).
- Functionally, `with_retry` is a strict superset of `retry_legacy`: configurable `max_attempts`, exponential backoff with `base_delay * 2^attempt`, optional jitter, and a configurable exception filter via `on=`. The task explicitly asks for "exponential backoff" — `retry_legacy` only sleeps a flat `1` second and cannot satisfy the spec.
- `with_retry` works as both a decorator and a function wrapper (`decorator if fn is None else decorator(fn)`), so applying it as a decorator on `BarClient` methods is idiomatic.

Do **not** touch `legacy_retry.py` or `foo.py` — out of scope, and migrating `foo.py` belongs to ticket #4421.

## 2. What "transient 5xx and connection errors" means here

`BarClient` uses `requests`. The natural exception set:

- `requests.exceptions.ConnectionError` — TCP / DNS / reset failures.
- `requests.exceptions.Timeout` — read / connect timeouts.
- `requests.exceptions.HTTPError` raised by `resp.raise_for_status()` — but only when `resp.status_code >= 500`. 4xx must NOT be retried (those are not transient).

`with_retry`'s `on=` parameter takes a single exception type (or tuple). To get "5xx OR connection error OR timeout" without retrying 4xx, the cleanest approach is a small **predicate-style retryable-exception class** — i.e. catch a custom exception and convert non-retryable errors before they reach the decorator.

Concretely, wrap each request in a tiny helper that:
1. Performs `requests.get(...)`.
2. If `resp.status_code >= 500`, raises `_TransientHTTPError` (a new internal exception).
3. Otherwise calls `raise_for_status()` (which surfaces 4xx as a normal `HTTPError`, NOT retried).
4. Returns `resp.json()`.

Then decorate that helper with `@with_retry(on=(_TransientHTTPError, requests.exceptions.ConnectionError, requests.exceptions.Timeout))`.

This keeps the 4xx-vs-5xx distinction explicit and local to `bar.py` rather than smuggling logic into a shared helper.

## 3. Files to modify

### 3a. `src/clients/bar.py` — MODIFY

Replace current contents with:

```python
import requests
from src.util.retry import with_retry


class _TransientHTTPError(Exception):
    """Raised internally for 5xx responses so with_retry can catch them.
    4xx responses are surfaced as normal requests.HTTPError and not retried."""


_RETRYABLE = (
    _TransientHTTPError,
    requests.exceptions.ConnectionError,
    requests.exceptions.Timeout,
)


@with_retry(on=_RETRYABLE)
def _get_json(url):
    resp = requests.get(url)
    if resp.status_code >= 500:
        raise _TransientHTTPError(f"{resp.status_code} from {url}")
    resp.raise_for_status()
    return resp.json()


class BarClient:
    def __init__(self, base_url):
        self.base_url = base_url

    def get_gadget(self, gadget_id):
        return _get_json(f"{self.base_url}/gadgets/{gadget_id}")

    def list_gadgets(self):
        return _get_json(f"{self.base_url}/gadgets/")
```

Design notes for the implementer:

- `_get_json` is module-level (not a method) so the `@with_retry` decorator wraps it exactly once at import time, not per-instance. This also keeps `__init__` untouched, as required.
- The leading underscore signals "internal to this module" — no API surface change.
- Keep `with_retry`'s defaults for `max_attempts=3`, `base_delay=0.5`, `jitter=True`. The task didn't request custom tuning; per the project's "Simplicity First" / "Surgical Changes" norms, don't introduce config knobs that weren't asked for.
- Import path is `from src.util.retry import with_retry` to match the existing test import style (`from src.clients.bar import BarClient`).

### 3b. `src/clients/legacy_retry.py` — DO NOT MODIFY
Owned by ticket #4421.

### 3c. `src/clients/foo.py` — DO NOT MODIFY
Out of scope; migration of `foo.py` is also ticket #4421.

### 3d. `src/util/retry.py` — DO NOT MODIFY
Already provides everything needed.

## 4. Tests to add / update

### 4a. `tests/clients/test_bar_client.py` — UPDATE

Keep the existing happy-path test working. The current test patches `src.clients.bar.requests.get`; after the refactor, `requests.get` is called from `_get_json` (still in `src.clients.bar`), so the same patch target continues to work. One small update: the existing test does `mock_get.return_value.raise_for_status = MagicMock()` but does not set `status_code`. After the change, `_get_json` reads `resp.status_code` before calling `raise_for_status`. Fix:

```python
def test_get_gadget_returns_json():
    with patch('src.clients.bar.requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"id": "g1"}
        mock_get.return_value.raise_for_status = MagicMock()
        result = BarClient("https://api.example.com").get_gadget("g1")
        assert result == {"id": "g1"}
```

### 4b. New tests in the same file

Add these cases. All use `patch('src.clients.bar.requests.get')` and `patch('src.clients.bar.time.sleep')` (or patch `time.sleep` inside `src.util.retry`) to keep tests fast.

1. **`test_list_gadgets_returns_json`** — mirror of the happy path for `list_gadgets`, asserts URL is `.../gadgets/`.

2. **`test_get_gadget_retries_on_5xx_then_succeeds`**
   - `mock_get.side_effect` returns two responses with `status_code=503` then one with `status_code=200` and `json()={"id":"g1"}`.
   - Assert final result equals `{"id":"g1"}` and `mock_get.call_count == 3`.

3. **`test_get_gadget_retries_on_connection_error_then_succeeds`**
   - `mock_get.side_effect = [requests.exceptions.ConnectionError(), MagicMock(status_code=200, json=lambda: {"id":"g1"}, raise_for_status=lambda: None)]`.
   - Assert `mock_get.call_count == 2` and result is `{"id":"g1"}`.

4. **`test_get_gadget_does_not_retry_on_4xx`**
   - Single response with `status_code=404` and `raise_for_status` raising `requests.exceptions.HTTPError`.
   - Assert `pytest.raises(requests.exceptions.HTTPError)` and `mock_get.call_count == 1`.

5. **`test_get_gadget_gives_up_after_max_attempts`**
   - All responses return `status_code=500`.
   - Assert `pytest.raises(Exception)` (specifically `_TransientHTTPError`, but importing it from `src.clients.bar` is fine since tests are internal) and `mock_get.call_count == 3` (matches `with_retry`'s default `max_attempts=3`).

6. **`test_init_does_not_call_requests`** (guards the "don't add retry to `__init__`" requirement)
   - Construct `BarClient("https://x")` inside the patch and assert `mock_get.call_count == 0`.

For tests 2, 3, 5: patch `time.sleep` (e.g. `with patch('src.util.retry.time.sleep')`) so the suite doesn't actually wait through exponential backoff.

## 5. How this respects the existing project

- **Reuses the canonical helper**, advancing the deprecation of `legacy_retry.py` instead of regressing it.
- **No new modules, no new config surface**: one decorated module-level function plus one internal exception class. Matches the "Simplicity First" / "Surgical Changes" guidelines.
- **Public API of `BarClient` is unchanged** — same class name, same method signatures, same return shapes. Existing callers and the existing test continue to pass with a one-line update for `status_code`.
- **`__init__` is untouched**, per the explicit task constraint.
- **4xx errors keep their current behavior** (raised immediately via `raise_for_status`) — only genuine transients are retried, which matches the stated intent.
- **Defaults inherited from `with_retry`** (`max_attempts=3`, `base_delay=0.5`, `jitter=True`) — no speculative tuning.

## 6. Implementation checklist (for the implementer)

1. Edit `src/clients/bar.py` per section 3a → verify: `python -c "from src.clients.bar import BarClient; print('ok')"` prints `ok`.
2. Update existing test in `tests/clients/test_bar_client.py` per 4a → verify: `pytest tests/clients/test_bar_client.py::test_get_gadget_returns_json -q` passes.
3. Add the six new tests per 4b → verify: `pytest tests/clients/test_bar_client.py -q` shows 7 passing.
4. Run the full suite → verify: no regressions in `foo.py` / `legacy_retry.py` tests (none touched).
