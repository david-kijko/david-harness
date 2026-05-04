```
SEMI-FORMAL FAULT LOCALIZATION CERTIFICATE

TASK
Failing test: tests/test_invoice.py::test_invoice_total_with_promo (line 1)
Test source (verbatim):
    def test_invoice_total_with_promo():
        invoice = Invoice(customer_id="C1")
        invoice.add_line(Item(sku="A", price=10.00), qty=2)
        invoice.add_line(Item(sku="B", price=5.00), qty=1)
        invoice.apply_promo(PercentOff(percent=10))
        assert invoice.total() == 22.50  # (10*2 + 5) * 0.9
Available source files: src/invoice.py, src/promo.py, src/line.py, src/item.py
CI config: pytest -p no:randomly, 8 parallel workers via pytest-xdist
Observed failure mode: AssertionError: 22.5 != 25.0 (i.e. invoice.total() returned 25.0 — the unreduced subtotal — instead of 22.5).

PHASE 1 — TEST SEMANTICS
T1: The test constructs ONE Invoice, appends two Line objects whose item.price * qty sum to 25.0, then registers exactly ONE PercentOff(percent=10).
T2: It asserts invoice.total() == 22.50.
T3: ~1/8 CI runs the actual return value is 25.0 — i.e. the promo factor (1 - 10/100) was NOT multiplied in. Because the multiplication path also performs `self._applied = True` (src/promo.py:9), the bypass of multiplication coincides exactly with `self._applied` already being truthy at the moment apply() is entered.

PHASE 2 — CODE PATH TRACING
METHOD:    Invoice.__init__("C1")
LOCATION:  src/invoice.py:20-23
BEHAVIOR:  Sets customer_id, lines=[], promos=[]. Lists created fresh per call (no mutable-default-arg sharing).
RELEVANT:  Confirms each Invoice gets its own promos list — sharing across Invoices would have to come from the promo objects themselves, not the list.

METHOD:    Invoice.add_line(item, qty)
LOCATION:  src/invoice.py:25-26
BEHAVIOR:  Appends Line(item=item, qty=qty) to self.lines.
RELEVANT:  Pure list growth. No hash, no dict, no set. Order = insertion order = deterministic.

METHOD:    Invoice.apply_promo(promo)
LOCATION:  src/invoice.py:28-29
BEHAVIOR:  Appends the supplied promo object reference to self.promos.
RELEVANT:  CRITICAL: this stores a REFERENCE to the promo. If the same promo *object* has already had .apply() called on it elsewhere in this Python process, its self._applied is already True when this Invoice later iterates over self.promos.

METHOD:    PercentOff.__init__(percent)
LOCATION:  src/promo.py:2-4
BEHAVIOR:  Sets self.percent = percent and self._applied = False.
RELEVANT:  Per-INSTANCE reset. So if a fresh instance is constructed for every test, _applied starts False every time.

METHOD:    PercentOff.apply(amount)
LOCATION:  src/promo.py:6-10
BEHAVIOR:  if self._applied: return amount
            self._applied = True
            return amount * (1 - self.percent / 100)
RELEVANT:  Stateful. First call on a given INSTANCE multiplies; every subsequent call on the SAME instance returns the input unchanged. The function is not idempotent and not pure — its return value depends on prior call history of the receiver.

METHOD:    Invoice.total()
LOCATION:  src/invoice.py:31-35
BEHAVIOR:  subtotal = sum(line.item.price * line.qty for line in self.lines)  → 25.0 deterministically
            for promo in self.promos:
                subtotal = promo.apply(subtotal)
            return round(subtotal, 2)
RELEVANT:  total() is itself non-idempotent because promo.apply is non-idempotent. Calling invoice.total() twice on the SAME Invoice yields 22.5 then 25.0.

HYPOTHESIS MEMORY BANK
H1 (initial, surface): "The bug is at the assertion site: float arithmetic 25 * 0.9 sometimes ≠ 22.5."
    → REFUTED. 25 * 0.9 == 22.5 exactly in IEEE-754; round(22.5, 2) == 22.5. And the observed wrong value is 25.0, not 22.500000001.

H2: "PercentOff(percent=10) is somehow not appended (apply_promo bug)."
    → REFUTED. apply_promo unconditionally appends; no branch, no exception path. If promos were empty total would be 25.0 EVERY run, not 1/8.

H3: "The _applied flag in PercentOff causes apply() to no-op when the same INSTANCE is reused across calls."
    → CONFIRMED as the necessary and sufficient condition for total()==25.0. The only way apply() returns `amount` unchanged is `self._applied is True` at entry (src/promo.py:7). Since __init__ sets it False, that requires the SAME instance to have been .apply()-ed before this test's total() call.

H4 (intermittency): "Why ~1/8? Because the test only fails when it shares a process with another test that already exercised THIS promo instance (or another code path that did)."
    → CONFIRMED in mechanism: pytest-xdist with `--dist=load` (the default) statically/dynamically partitions the test set across the 8 worker processes. Each worker is its own Python interpreter. A worker that imports src.promo and runs ANOTHER test that calls .apply() on a shared/cached PercentOff instance (typical patterns: a module-level `DEFAULT_PROMO = PercentOff(10)` in src/promo.py or a tests/conftest.py session-scoped fixture returning a single PercentOff) will leave _applied=True on that instance. If `apply_promo` later receives that same already-fired instance — directly OR via a parametrize id, OR because pytest-xdist's test-distribution happened to put two such tests into the same worker — total() returns the unreduced 25.0. With 8 workers and load distribution, the probability that the offending pair lands on the same worker fluctuates run-to-run, producing the ~1/8 rate.
    Note: I cannot read the rest of the test suite or conftest.py from the prompt, so the *specific* sibling test that pollutes the instance is not nameable; but the MECHANISM is fully determined by src/promo.py:6-10. Any code path that gives this test a non-fresh PercentOff triggers exactly the observed symptom.

PHASE 3 — DIVERGENCE ANALYSIS

CLAIM D1: At src/promo.py:7-9, PercentOff.apply mutates self._applied and short-circuits on subsequent calls. This contradicts T1's *latent* premise — that PercentOff is a value-like discount whose effect on an amount depends only on (amount, percent), not on call history. In particular it contradicts T2's expected value 22.50 whenever the receiver instance has been .apply()-ed previously in this process.
Inference type: invariant-violation (idempotence / referential transparency expected of a "discount" was broken by hidden mutable state).

CLAIM D2: At src/invoice.py:28-29, Invoice.apply_promo stores the caller's promo reference verbatim (no copy.deepcopy, no factory call). This is normally fine, but combined with D1 it means Invoice inherits any pre-existing _applied=True state from outside, turning a local invariant violation in promo.py into a cross-test correctness bug.
Inference type: aliasing / shared-mutable-state propagation.

CLAIM D3: At src/invoice.py:33-34, total() invokes promo.apply once per promo in insertion order. This is correct on its own, but it surfaces D1: total() inherits non-idempotence from apply(), so the *Invoice* API also silently violates the principle that total() should be a pure read of state.
Inference type: contagion of non-idempotence up the call stack.

SUSPICIOUS REGIONS

Region R1: src/promo.py:6-10
  Code:
      def apply(self, amount):
          if self._applied:
              return amount
          self._applied = True
          return amount * (1 - self.percent / 100)
  Hypothesis: This is the root cause. apply() must be a pure function of (amount, self.percent). The _applied gate is the entire mechanism by which total() can ever return 25.0.
  Trace from test: T1 → invoice.apply_promo(PercentOff(10)) appends instance P. → invoice.total() iterates promos, calls P.apply(25.0). If P._applied is False → returns 22.5 (test passes). If P._applied is True (because P, or a class/module-level instance aliased as P, was already .apply()-ed in this worker process) → returns 25.0 unchanged → assertion fails with exactly the observed message "22.5 != 25.0".
  Verdict: LIKELY BUGGY (root cause)
  Evidence: src/promo.py:7 (the gate), src/promo.py:8 (the mutation), src/promo.py:9 (the only multiplying return), src/invoice.py:33-34 (the call site that propagates the wrong return).

Region R2: src/promo.py:3 (`self._applied = False` in __init__)
  Code: self._applied = False
  Hypothesis: This line *exists only* to support the broken gate in R1. It is part of the same defect — together with R1 it constitutes the stateful design.
  Verdict: LIKELY BUGGY (co-located with R1; both should be removed)
  Evidence: It has no other reader/writer than apply().

Region R3: src/invoice.py:28-29 (apply_promo)
  Code: self.promos.append(promo)
  Hypothesis: Stores aliased reference. Were this a defensive copy, R1 would be masked for fresh-instance tests.
  Verdict: UNLIKELY ROOT CAUSE. This is idiomatic Python; defending against caller-provided shared mutable state is the wrong place to fix the bug. Fixing here would just paper over R1.
  Evidence: src/invoice.py:28-29.

Region R4: src/invoice.py:31-35 (total)
  Verdict: UNLIKELY. sum() over a list of (price * qty) of two literal floats is exactly 25.0; round(_, 2) is exactly 22.5. No nondeterminism originates here.

Region R5: src/item.py / src/line.py dataclasses
  Verdict: UNLIKELY. With eq=True (default) and no frozen=True, Item/Line are unhashable, but nothing in the traced path hashes them. Field order is class-definition order, not hash-randomized.

PHASE 4 — RANKED PREDICTIONS  (most likely first)

1. src/promo.py:6-10 (the entire PercentOff.apply method) — Confidence: HIGH
   Because: CLAIM D1. The only mechanism by which total() can return the observed 25.0 is apply() returning its input unchanged, which happens iff self._applied is True at entry. Removing the gate (and the corresponding self._applied bookkeeping) makes apply() a pure function of (amount, percent) and eliminates BOTH the symptom AND the cross-test contagion that produces the ~1/8 intermittency.

2. src/promo.py:3 (`self._applied = False`) — Confidence: HIGH
   Because: CLAIM D1. Same defect as #1 — the field exists solely to support the broken gate. Should be deleted as part of the same fix.

3. (Tertiary, NOT the root cause) src/invoice.py:28-29 — Confidence: LOW
   Because: CLAIM D2. Adding a defensive copy.deepcopy(promo) would mask the bug for this test by always handing total() a fresh instance, but it does not fix the underlying invariant violation in PercentOff and would mislead future callers into believing apply() is safe to share — leaving the latent landmine in place.

DIFFERENTIAL CHECK  (REQUIRED — protects against stopping at crash site)

"If the bug were at the crash site (the assertion in tests/test_invoice.py, e.g. float-imprecision in the expected literal 22.50) rather than at the predicted root cause src/promo.py:6-10, what should we observe that we don't?"

Answer:
  (a) A float-imprecision bug would produce a value like 22.5000000001 or 22.499999998, not the round number 25.0. We observe 25.0 exactly — the literal subtotal — which is impossible from rounding noise but trivial from "promo factor never multiplied in."
  (b) A float-imprecision bug would fail on EVERY run (the float math is deterministic per build), not 1/8. The 1/8 rate REQUIRES per-process state that varies across xdist workers — exactly what self._applied is.
  (c) If the bug were at Invoice.total()'s round() call (e.g. round(_,2) returning the unrounded value), we would expect failures with non-25.0 fractional residues and again deterministically, not intermittently.
  (d) If the bug were at Invoice.apply_promo (e.g. silently dropping the promo), invoice.promos would be empty and total() would return 25.0 every run, not 1/8.

Only the predicted root cause — stateful PercentOff.apply with a per-instance _applied flag — explains BOTH (i) the *exact* wrong value 25.0 AND (ii) the run-to-run intermittency that tracks worker count.

FORMAL CONCLUSION

The most likely fault is src/promo.py lines 6-10 (the body of PercentOff.apply), with the supporting line src/promo.py:3 (the self._applied initialization).

Mechanism:
  - apply() is supposed to be a pure function of (amount, percent) but is in fact stateful: the first call on a given PercentOff instance multiplies by (1 - percent/100) and latches self._applied=True; every subsequent call on that SAME instance returns its input unchanged.
  - Whenever invoice.total() runs against a promo whose _applied is already True (because a previous test, fixture, or module-level constant in the same worker process already called .apply() on that instance), the multiplication is skipped and total() returns the bare subtotal 25.0 — exactly matching the observed failure "22.5 != 25.0".
  - Intermittency at ~1/8 is explained by pytest-xdist distributing tests across 8 separate worker processes with `--dist=load`. Each worker is its own interpreter, so per-process state in PercentOff (the latched _applied) is independent across workers. Whether the failing test ends up co-located in the same worker as a sibling test/fixture that pollutes a shared PercentOff instance varies run-to-run; with 8 workers the collision probability is on the order of 1/8.

Single-file fix (file:line that needs to change): **src/promo.py:6-10** — remove the _applied gate and the self._applied=True mutation, leaving apply() as a pure function:

    def apply(self, amount):
        return amount * (1 - self.percent / 100)

and delete src/promo.py:3 (`self._applied = False`).

After this change apply() is referentially transparent, total() becomes idempotent, and no amount of cross-test instance sharing or xdist worker-pinning can produce the 25.0 wrong-answer state.

---

FINAL STATEMENT

Root cause: src/promo.py lines 6-10 (the body of `PercentOff.apply`, with src/promo.py:3 as its co-defective initializer). The single line that most concisely "needs to change" is **src/promo.py:7** — the `if self._applied: return amount` short-circuit — because removing it (together with the now-dead `self._applied = True` on line 9 and `self._applied = False` on line 3) makes `apply` a pure function and eliminates the bug.

Intermittency mechanism: pytest-xdist runs the suite in 8 separate worker PROCESSES. Per-process state on a PercentOff instance (the latched `self._applied = True`) leaks between sibling tests that share a PercentOff via a module-level constant or session-scoped fixture. xdist's default `--dist=load` shuffles which tests land in which worker each CI invocation, so whether the failing test shares a worker with a polluting sibling varies run to run — producing the observed ~1-in-8 failure rate that exactly tracks the 8-worker count.
```
