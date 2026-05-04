# Bench2 — Fault Localization

## Root cause

**File:line:** `src/promo.py:43` (the `self._applied = False` flag), with the
guarded branch at `src/promo.py:46-48` (`if self._applied: return amount`).

The `PercentOff` class carries **mutable per-instance state** (`_applied`) that
permanently disables the discount after the first call to `apply()`. A value
object representing "10% off" should be stateless / idempotent; instead, this
one mutates itself on first use and silently becomes a no-op on every
subsequent use.

```python
# src/promo.py
class PercentOff:
    def __init__(self, percent):
        self.percent = percent
        self._applied = False        # <-- line 43, the offending state

    def apply(self, amount):
        if self._applied:            # <-- line 46
            return amount            # <-- line 47: silently skips the discount
        self._applied = True         # <-- line 48
        return amount * (1 - self.percent / 100)
```

When `apply()` is called on an instance whose `_applied` is already `True`,
it returns the subtotal **unchanged** — exactly the observed failure mode:

- expected: `22.50` = `(10*2 + 5) * 0.9`
- actual:   `25.00` = `(10*2 + 5)`     ← discount was skipped

That delta (`22.5` vs `25.0`) is the literal symptom in the failing assertion.

## Mechanism of intermittency (why ~1 in 8)

The test as written constructs a fresh `PercentOff(percent=10)`, so on its
own it should never observe `_applied == True`. The intermittency therefore
comes from **instance sharing across tests inside a single worker process**,
combined with `pytest-xdist`'s scheduling.

The mechanism:

1. Somewhere else in the suite (a `conftest.py` fixture, a module-level
   constant such as `STANDARD_PROMO = PercentOff(percent=10)`, or a
   parameterised test that imports a shared promo), the **same**
   `PercentOff` instance is handed to more than one test.
2. The first test that touches it calls `apply()` once and flips
   `_applied` to `True` — permanently, for the lifetime of that worker
   process.
3. Any later test in that worker that uses **that same instance** then
   gets the un-discounted amount back.

Why exactly ~1/8:

- `pytest-xdist` with 8 workers distributes tests across 8 long-lived
  worker processes. The default `--dist=load` scheduler hands tests to
  whichever worker is idle, so the *worker assignment* of any given test
  is effectively non-deterministic from run to run, even with
  `-p no:randomly` (which only fixes the *order within a worker*, not
  *which* worker gets a test).
- For `test_invoice_total_with_promo` to fail, it must (a) land on the
  same worker as the test that pre-tainted the shared `PercentOff`, and
  (b) run after it. With 8 workers and one "poisoner" test, the
  co-location probability is ~1/8 — matching the observed failure rate.
- The other 7/8 of runs, the poisoner lands on a different worker; the
  worker running our test sees a clean `_applied = False` and the
  discount is applied normally.

`-p no:randomly` masks the bug locally (single process, deterministic
order means either it always fails or always passes for a given file),
which is why it only shows up under xdist in CI.

## Fix

Remove the stateful guard entirely — `PercentOff.apply` should be a pure
function of its inputs:

```python
# src/promo.py
class PercentOff:
    def __init__(self, percent):
        self.percent = percent

    def apply(self, amount):
        return amount * (1 - self.percent / 100)
```

If single-application semantics are genuinely required, enforce it on the
**`Invoice`** side (e.g., dedupe `self.promos` or track applied promos on
the invoice, not on the promo object itself), so the value object stays
stateless and safe to share.

## Verification status

UNVERIFIED at runtime: this benchmark ships only `prompt.md` (no `src/`
or `tests/` tree on disk to execute), so I could not run the failing
test. The diagnosis is from static reading of the code in the prompt;
the float arithmetic was sanity-checked (`round(25.0 * 0.9, 2) == 22.5`)
to rule out a numeric cause and confirm `25.0` can only arise from the
discount being skipped.
