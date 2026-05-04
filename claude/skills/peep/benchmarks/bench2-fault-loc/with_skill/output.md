SEMI-FORMAL FAULT LOCALIZATION CERTIFICATE

TASK
Failing test: tests/test_invoice.py :: test_invoice_total_with_promo
Test source (verbatim):
```
def test_invoice_total_with_promo():
    invoice = Invoice(customer_id="C1")
    invoice.add_line(Item(sku="A", price=10.00), qty=2)
    invoice.add_line(Item(sku="B", price=5.00), qty=1)
    invoice.apply_promo(PercentOff(percent=10))
    assert invoice.total() == 22.50  # (10*2 + 5) * 0.9
```
Available source files (per prompt): src/invoice.py, src/promo.py, src/line.py, src/item.py, tests/test_invoice.py.
Environment: pytest with `-p no:randomly` (random ordering disabled) and 8 parallel workers via pytest-xdist.

PHASE 1 — TEST SEMANTICS (formal premises)
T1: The test constructs a NEW Invoice, adds two lines (10.00 x 2 and 5.00 x 1), then constructs a NEW PercentOff(percent=10) inline and applies it.
T2: The test asserts `invoice.total() == 22.50`. Expected math: (10*2 + 5) * 0.9 = 22.5.
T3: Observed failure mode in CI: `AssertionError: 22.5 != 25.0` on roughly 1 in 8 runs. 25.0 is exactly the un-discounted subtotal — i.e. the discount was NOT applied on those runs.

REACHABILITY GATE  (mandatory — guards against fabricated state assumptions)

S1: "PercentOff instance is fresh with `_applied = False` at the moment `apply()` is called."
     Evidence in prompt: tests/test_invoice.py line `invoice.apply_promo(PercentOff(percent=10))` constructs a new instance inline; src/promo.py `__init__` sets `self._applied = False`.
     Status: VERIFIED.

S2: "The PercentOff instance used by this test is shared with another test / fixture / module-level singleton, so `_applied` may already be True when this test runs."
     Evidence in prompt: NONE. The prompt shows only this one test, no fixtures, no conftest, no module-level instances. The test literally constructs `PercentOff(percent=10)` on its own line.
     Status: hypothesis — unverified.

S3: "pytest-xdist workers share mutable Python state across the 8 worker processes."
     Evidence in prompt: NONE. pytest-xdist runs each worker in a separate OS process; module-level state is per-process. The prompt does not show any cross-process sharing mechanism (no Manager, no file, no DB).
     Status: hypothesis — unverified (and contradicted by standard xdist semantics).

S4: "Within a single worker process, a previous test in the same suite mutates a shared PercentOff before this test runs, causing `_applied=True` to leak in."
     Evidence in prompt: NONE. Only one test is shown. No other tests, no fixtures, no shared module-level promo instance are exhibited. This is a plausible-but-unverified explanation for the 1-in-8 cadence.
     Status: hypothesis — unverified.

S5: "Within this test, `apply()` is invoked more than once on the same PercentOff instance, so the SECOND call sees `_applied=True` and returns the subtotal unchanged."
     Evidence in prompt: src/invoice.py `total()` iterates `self.promos` once and calls `promo.apply(subtotal)` once per promo. The test calls `total()` exactly once and `apply_promo` exactly once. So under the prompt as written, `apply()` is invoked exactly once.
     Status: REFUTED for the single-test single-call path. Would only become VERIFIED if there were a second `total()` call or duplicate append (no evidence of either).

Predictions tagged below carry the `(depends on hypothesis S[N])` marker where applicable, and list the evidence that would upgrade them.

PHASE 2 — CODE PATH TRACING
METHOD: Invoice.__init__(customer_id="C1")
LOCATION: src/invoice.py (Invoice.__init__)
BEHAVIOR: sets self.customer_id, self.lines = [], self.promos = []. Per-instance lists — not class attributes (verified by reading the code).
RELEVANT: confirms a fresh Invoice has empty lines/promos.

METHOD: Invoice.add_line(item, qty)  (called twice)
LOCATION: src/invoice.py (Invoice.add_line)
BEHAVIOR: appends Line(item=item, qty=qty) to self.lines.
RELEVANT: after the two calls, self.lines has Line(Item("A",10.00), 2) and Line(Item("B",5.00), 1).

METHOD: PercentOff.__init__(percent=10)
LOCATION: src/promo.py (PercentOff.__init__)
BEHAVIOR: sets self.percent=10, self._applied=False (instance attribute, set unconditionally on every construction).
RELEVANT: every freshly constructed PercentOff has _applied=False at construction time.

METHOD: Invoice.apply_promo(promo)
LOCATION: src/invoice.py (Invoice.apply_promo)
BEHAVIOR: appends promo to self.promos. No mutation of promo, no copy.
RELEVANT: self.promos becomes [<that PercentOff instance>].

METHOD: Invoice.total()
LOCATION: src/invoice.py (Invoice.total)
BEHAVIOR:
  subtotal = sum(line.item.price * line.qty for line in self.lines)  # 10.00*2 + 5.00*1 = 25.0
  for promo in self.promos: subtotal = promo.apply(subtotal)         # one promo, one call
  return round(subtotal, 2)
RELEVANT: under the inputs in the test, exactly ONE call to PercentOff.apply with amount=25.0.

METHOD: PercentOff.apply(amount)
LOCATION: src/promo.py (PercentOff.apply)
BEHAVIOR:
  if self._applied: return amount      # short-circuit returns input unchanged
  self._applied = True
  return amount * (1 - self.percent / 100)
RELEVANT: returns the discounted value if and only if self._applied was False on entry. If self._applied was True on entry, returns 25.0 verbatim, which matches the observed failure value.

PHASE 3 — DIVERGENCE ANALYSIS

CLAIM D1 (invariant-violation): At src/promo.py PercentOff.apply, the `_applied` short-circuit makes the promo a one-shot. The promo correctly discounts only on the FIRST `apply()` call across the lifetime of the instance and silently returns the input for every subsequent call. This is a divergence from the implicit contract that "applying a percent-off promo to a subtotal returns the discounted subtotal." T2 expects the discounted subtotal whenever `total()` is called, with no global "already-applied" memory.

CLAIM D2 (latent-coupling): Because `_applied` is per-instance state on PercentOff, the promo's correctness is no longer a pure function of (amount, percent). It is now a function of (amount, percent, prior call history of THIS instance). Any code path that re-uses the same PercentOff instance — across multiple `total()` calls, across multiple invoices, or across tests via a shared fixture — silently produces wrong (un-discounted) totals on the second and later applications. This contradicts T2 and is the structural reason the bug is intermittent rather than deterministic.

CLAIM D3 (intermittency-mechanism, hypothesis): The 1-in-8 failure cadence requires SOME mechanism that sometimes presents an already-applied PercentOff to this test's `apply()`. Candidates not supported by the prompt but consistent with the symptom: (a) S4 — a shared-fixture PercentOff in a conftest not shown in the prompt; (b) a parametrized or repeated test that constructs and applies one PercentOff and reuses it; (c) a worker-local module-level cache of promos. None of these are exhibited in the prompt; they are listed only to make the hypothesis-vs-evidence boundary explicit.

SUSPICIOUS REGIONS

Region R1: src/promo.py — the `_applied` flag and its short-circuit (the `__init__` line `self._applied = False` plus the `apply` body's `if self._applied: return amount; self._applied = True`).
  Code (paste):
    class PercentOff:
        def __init__(self, percent):
            self.percent = percent
            self._applied = False

        def apply(self, amount):
            if self._applied:
                return amount
            self._applied = True
            return amount * (1 - self.percent / 100)
  Hypothesis: This stateful one-shot logic is the bug per CLAIM D1/D2. A correct PercentOff.apply is a pure function: `return amount * (1 - self.percent / 100)`. Removing `_applied` makes `apply()` idempotent and reusable; under any sharing pattern (S2/S4) the test would then return 22.5 deterministically.
  Trace from test: T1 constructs PercentOff -> apply_promo stores it -> total() calls apply(25.0). With `_applied=False` on entry, returns 22.5; with `_applied=True` on entry (only possible via reuse not shown in the prompt), returns 25.0 — exactly matching T3.
  Verdict: LIKELY BUGGY (root cause of the wrong value 25.0).
  Evidence: the failure value 25.0 equals the un-discounted subtotal exactly; the only branch in src/promo.py that yields the input unchanged is the `if self._applied: return amount` branch.

Region R2: src/invoice.py Invoice.total — calls promo.apply once per `total()` invocation; no caching, no double iteration.
  Verdict: UNLIKELY buggy. Every line traces correctly to T1/T2 under the inputs given.
  Evidence: inspection of Invoice.total shows a single `for promo in self.promos: subtotal = promo.apply(subtotal)` and a single return.

Region R3: src/invoice.py Invoice.apply_promo / add_line / __init__ — all three are straightforward appends/assignments.
  Verdict: UNLIKELY buggy.

Region R4: src/line.py / src/item.py — plain dataclasses, no behavior beyond field storage.
  Verdict: UNLIKELY buggy.

PHASE 4 — RANKED PREDICTIONS  (most likely first)

1. src/promo.py — the `_applied` flag in PercentOff (the `self._applied = False` initialization plus the `if self._applied: return amount; self._applied = True` short-circuit in `apply`). Confidence: HIGH for "this is the wrong value's source"; MEDIUM for "this is the *intermittency* mechanism" because the latter depends on hypothesis S2/S4.
   Because: CLAIM D1 establishes that this is the only branch in any cited source file that returns the input subtotal unchanged, and 25.0 is exactly the un-discounted subtotal. CLAIM D2 explains why the bug is latent: under the single-test-single-call path shown in the prompt the bug is invisible, but any reuse of the instance flips the behavior. The fix is to delete `_applied` entirely and make `apply` a pure function.

2. (depends on hypothesis S2/S4) A not-shown conftest fixture, parametrization, or shared module-level PercentOff that causes the same instance to be apply()'d before this test's `total()` runs. Confidence: LOW-MEDIUM as a *separate* fault site; this is really the *trigger* for fault #1, not a fault on its own.
   Because: 1-in-8 intermittency on otherwise-deterministic code requires either shared state across runs/tests or a non-deterministic ordering. Evidence to upgrade S2/S4 to VERIFIED would be: a conftest.py showing a session- or module-scoped `percent_off` fixture, OR another test that reuses the same PercentOff instance, OR test parametrization that loops the same instance through multiple invoices.

3. src/invoice.py Invoice.total — Confidence: LOW.
   Because: no claim D[N] indicts this code; it is a straight pass-through that calls apply exactly once per promo in self.promos.

DIFFERENTIAL CHECK  (REQUIRED — protects against stopping at crash site)
"If the bug were at the assert site (tests/test_invoice.py — i.e. wrong expected value, or wrong test arithmetic) rather than at src/promo.py PercentOff.apply, what should we observe that we don't?"
- We should observe a DETERMINISTIC failure on every CI run (the test arithmetic is constant; (10*2+5)*0.9 = 22.5 is correct math). We instead observe an intermittent failure roughly 1 in 8 runs — incompatible with a constant-expected-value bug.
- We should observe the failure value being SOMETHING OTHER than the un-discounted subtotal (e.g. 22.49 from a rounding error, or 20.0 from a wrong percent). Instead we observe exactly 25.0, which equals `sum(line.item.price * line.qty)` to the cent — the unique value produced by the `if self._applied: return amount` branch in src/promo.py.
- If the bug were in Invoice.total's iteration (e.g. iterating self.promos zero times sometimes), we would also see 25.0, BUT the only way Invoice.total skips the loop is if self.promos is empty — and `apply_promo` is unconditionally called on a fresh Invoice. There is no code path in Invoice that empties self.promos. So Invoice.total is excluded.
- The PercentOff `_applied` short-circuit is the ONLY code path among the cited files that produces 25.0 from a 25.0 subtotal with `self.promos == [a PercentOff(10)]`.

FORMAL CONCLUSION
The most likely fault is in src/promo.py — specifically the `_applied` instance flag in `PercentOff` (the `self._applied = False` line in `__init__` plus the `if self._applied: return amount` / `self._applied = True` lines in `apply`). It is the unique branch in the cited code that returns the subtotal unchanged, which matches the observed failure value 25.0 exactly (CLAIM D1 + differential check). The fix is to make `PercentOff.apply` a pure function — return `amount * (1 - self.percent / 100)` unconditionally and remove `_applied` — which eliminates the latent coupling identified in CLAIM D2.

The mechanism of the 1-in-8 intermittency is HYPOTHESIS-TAGGED (depends on S2/S4): the prompt does not exhibit any shared PercentOff instance, conftest fixture, parametrization, or other mechanism by which `_applied=True` could leak into this test's freshly-constructed promo. The most plausible unverified mechanism is a shared/session-scoped PercentOff fixture in a conftest not shown in the prompt, OR another test in the suite that constructs one PercentOff and reuses it across multiple Invoices; under pytest-xdist with 8 workers and load-balanced distribution, whether this test lands on the same worker as that polluting test (after that test has already run) governs the failure cadence and could plausibly produce a ~1/8 hit rate. This explanation would be upgraded to VERIFIED only by inspecting the full tests/ tree and any conftest.py — neither of which is in the prompt. Note also that S3 ("xdist workers share state") is contradicted by standard xdist semantics; the intermittency must come from intra-worker test interaction, not inter-worker.

FINAL STATEMENT
Root cause file:line — src/promo.py, the `PercentOff._applied` flag: the `self._applied = False` line inside `PercentOff.__init__` together with the three-line `if self._applied: return amount` / `self._applied = True` short-circuit at the top of `PercentOff.apply`. Fix: delete the `_applied` flag entirely and reduce `apply` to `return amount * (1 - self.percent / 100)`.

Intermittency mechanism (hypothesis — unverified, depends on S2/S4): a PercentOff instance is being reused across calls/tests somewhere not shown in the prompt (most likely a session- or module-scoped pytest fixture in a conftest.py, or another test in the suite that re-applies the same promo to multiple Invoices). On runs where the polluting use happens before this test runs on the same worker, `_applied` is already True when this test calls `total()`, the short-circuit fires, and the un-discounted 25.0 is returned. The fix above eliminates this hypothesis as a failure mode regardless of whether the sharing actually exists, because a stateless `apply()` cannot be poisoned by prior calls.
