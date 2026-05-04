# Bench3 — Code QA (with peep skill)

```
SEMI-FORMAL CODE ANALYSIS CERTIFICATE

QUESTION: In Python, what is the difference in observable behavior between
Implementation A (seen=set) and Implementation B (seen=list) of
unique_in_order across the four given inputs? For each disagreement,
identify the underlying language mechanism.

FUNCTION TRACE TABLE
| Function/Method | File:Line | Param Types | Return Type | Verified Behavior | Key Detail |
|---|---|---|---|---|---|
| unique_in_order (A) | prompt.md:3-9 | iterable of any | generator yielding items | Lazily yields each item the first time it appears (vs `seen: set`); membership test via `set.__contains__` | `seen.add(item)` requires `item.__hash__`; raises TypeError on unhashable input. Membership test is amortized O(1). |
| unique_in_order (B) | prompt.md:13-19 | iterable of any | generator yielding items | Lazily yields each item the first time it appears (vs `seen: list`); membership test via `list.__contains__` | `list.__contains__` requires only `__eq__`, never `__hash__`. Membership test is O(len(seen)) — overall O(n*k) where k = distinct seen so far. |
| set.__contains__ | CPython Objects/setobject.c (PyAnySet_Contains) | (set, obj) | bool | Hashes `obj`; if obj is unhashable raises `TypeError: unhashable type: '<type>'`; otherwise looks up by hash+eq. | Verified empirically: `list(A([[1,2],[1,2],[3]]))` → `TypeError: unhashable type: 'list'` (see /tmp/peep_results3.txt). |
| list.__contains__ | CPython Objects/listobject.c (list_contains) | (list, obj) | bool | Linear scan; calls PyObject_RichCompareBool(item, target, Py_EQ) for each element. Never invokes __hash__. | Works for any object that defines __eq__ (all do, by default identity). |
| frozenset.__hash__ | CPython Objects/setobject.c (frozenset_hash) | (frozenset) | int | Hash depends only on elements; `hash(frozenset({1,2})) == hash(frozenset({2,1}))` (verified, /tmp/peep_results3.txt). | This is what makes Test 2 yield only the first frozenset for both A and B. |
| frozenset.__eq__ | CPython Objects/setobject.c | (frozenset, frozenset) | bool | Equal iff same elements regardless of insertion order: `frozenset({1,2}) == frozenset({2,1})` → True (verified). | Both A and B see the second frozenset as a duplicate. |
| list.__eq__ | CPython Objects/listobject.c (list_richcompare) | (list, list) | bool | Element-wise equality, order-sensitive: `[1,2] == [1,2]` → True. | B detects [1,2] as duplicate. A never gets to compare because hashing fails first. |
| generator (PEP 255) | Python language spec | n/a | iterator | `yield` suspends the function; `next()` resumes until next yield or StopIteration. Caller-driven. | Caller controls how many items are produced. With an infinite source and only k unique values, asking for >k items blocks forever inside `next()`. |

DATA FLOW ANALYSIS

Variable: seen  (Implementation A)
- Created at: prompt.md:4 as `set()`
- Modified at: prompt.md:7 via `seen.add(item)`
- Used at: prompt.md:5 (`item not in seen` → set membership)
- Key constraint: every `item` must be hashable; otherwise the membership
  test raises TypeError before yield can occur.

Variable: seen  (Implementation B)
- Created at: prompt.md:14 as `[]`
- Modified at: prompt.md:17 via `seen.append(item)`
- Used at: prompt.md:15 (`item not in seen` → list membership, linear scan)
- Key constraint: every `item` must define `__eq__` (all Python objects do).
  No hashability required. Cost grows with number of unique items seen.

Variable: item
- Bound by: `for item in iterable` (prompt.md:5 / :15)
- Used at: membership test, mutation of `seen`, yielded to caller.
- Key constraint: A requires `item` hashable; B does not.

SEMANTIC PROPERTIES (with evidence)

SP1: A and B produce the same output sequence whenever every input
     element is hashable AND `__hash__`/`__eq__` are consistent.
     — Evidence: Test 1 verified (/tmp/peep_results3.txt) — both yield [1, 2, 3].
     — Inference type: by-construction. Both algorithms are "yield-on-first-
       seen with same equality relation"; they only differ in the data
       structure backing the membership predicate.

SP2: A raises TypeError when given an unhashable element; B does not.
     — Evidence: Test 3 verified — A error: `TypeError: unhashable type: 'list'`;
       B returns `[[1, 2], [3]]` (/tmp/peep_results3.txt).
     — Inference type: empirical-from-trace, grounded in
       `set.__contains__` requiring `__hash__`.

SP3: For frozensets that compare equal (and therefore hash equal by the
     frozenset contract), both A and B treat them as duplicates.
     — Evidence: Test 2 verified — A: `[frozenset({1,2}), frozenset({3,4})]`,
       B same. Also: `frozenset({1,2}) == frozenset({2,1})` is True and
       `hash(frozenset({1,2})) == hash(frozenset({2,1}))` is True
       (/tmp/peep_results3.txt).
     — Inference type: by-invariant — Python contract: `a == b` implies
       `hash(a) == hash(b)` when both are hashable.

SP4: With an infinite input, both A and B yield exactly the set of
     distinct values, then block forever inside `next()` of the generator
     consuming the input. They do not raise, do not return, do not get
     to the caller's next iteration.
     — Evidence: For input 0,1,0,1,..., only two distinct values exist.
       A and B yield 0 then 1, then their inner `for` loop consumes 0,1,0,1,...
       forever with the `if item not in seen` branch never taken, so they
       never reach `yield` again. Verified by running with bounded input
       (1000 items) and asking for 4 outputs: both produced [0, 1] only,
       consuming all 1000 inputs (/tmp/peep_results3.txt). On a truly
       infinite input the inner loop never terminates.
     — Inference type: by-construction — generator semantics + finite
       cardinality of distinct values.

SP5: B has worst-case time complexity O(n*k) where k = number of distinct
     items seen so far (linear membership scan per item). A is O(n)
     amortized.
     — Evidence: list_contains is a linear scan (CPython listobject.c);
       set membership is a hash lookup. Standard CS / CPython
       documentation.
     — Inference type: by-contract — documented data-structure complexity.

SP6: B's `seen` list preserves insertion order (which equals first-seen
     order). A's `seen` set has no insertion order semantics.
     This does NOT affect output for either implementation, because the
     output order is driven by `yield item` in input-iteration order, not
     by the structure of `seen`.
     — Evidence: Read of prompt.md lines 8 and 18 — both yield `item`
       directly, not anything derived from `seen`.
     — Inference type: by-construction.

ALTERNATIVE HYPOTHESIS CHECK  (REQUIRED — protects against confident-wrong)

Hypothesis Alt-1: "Test 2 (frozensets) is a disagreement because A uses a
set and B uses a list, so they handle frozensets differently."
  - Searched for: whether `frozenset.__hash__` is defined; whether
    `frozenset({1,2}) == frozenset({2,1})`.
  - Found: hash equal True, eq True, both A and B output the same 2-element
    list (verified, /tmp/peep_results3.txt).
  - Conclusion: REFUTED. Test 2 is an AGREEMENT, not a disagreement. The
    only thing that would have caused a disagreement is unhashability, and
    frozensets are hashable.

Hypothesis Alt-2: "Test 3 (lists of lists) — maybe B also fails because
unhashable lists can't be compared either."
  - Searched for: behavior of `list.__contains__` on unhashable items.
  - Found: `list.__contains__` only uses `__eq__`, not `__hash__`. Verified:
    `list(B([[1,2],[1,2],[3]]))` returns `[[1, 2], [3]]` with no error
    (/tmp/peep_results3.txt).
  - Conclusion: REFUTED. B succeeds; A fails. The mechanism is hashability
    requirement of `set`, not anything about lists-as-elements per se.

Hypothesis Alt-3: "Test 4 — A finishes faster than B, or one of them
behaves differently with infinite input due to the data-structure choice."
  - Searched for: whether either implementation can detect end-of-stream
    or short-circuit on infinite input.
  - Found: Both run the same `for item in iterable` loop. Neither has any
    termination logic beyond `iterable` exhausting. With only 2 distinct
    input values, both stop yielding after item #2 and then loop forever
    over the infinite input. Verified empirically with bounded input
    standing in for infinite (/tmp/peep_results3.txt).
  - Conclusion: REFUTED for "different observable output". Both yield
    exactly [0, 1], then both block forever; the caller never collects a
    3rd item, let alone a 4th. There is a *performance* difference in
    principle (A's set-add is O(1), B's list-append + membership scan is
    O(k)), but with k=2 it is unobservable. There is also a memory
    difference (set vs list of 2 small ints), again unobservable.

Hypothesis Alt-4: "Test 1 — could A and B disagree on order, since sets
are unordered?"
  - Searched for: where output order is determined.
  - Found: Output order is solely determined by the `yield item` line
    iterating over `iterable` in its native order. `seen` is consulted but
    never iterated. Verified: both output `[1, 2, 3]` (/tmp/peep_results3.txt).
  - Conclusion: REFUTED. Order of `seen` is irrelevant.

GROUNDED ANSWER

Per-input answer (each claim cites a trace-table row or SPn above):

INPUT 1: [1, 2, 1, 3, 2]
  - Implementation A → [1, 2, 3]   (verified, /tmp/peep_results3.txt)
  - Implementation B → [1, 2, 3]   (verified, /tmp/peep_results3.txt)
  - AGREE. Both ints are hashable and have consistent __hash__/__eq__,
    so SP1 applies.

INPUT 2: [frozenset({1,2}), frozenset({2,1}), frozenset({3,4})]
  - Implementation A → [frozenset({1,2}), frozenset({3,4})]   (verified)
  - Implementation B → [frozenset({1,2}), frozenset({3,4})]   (verified)
  - AGREE. By SP3: frozensets are hashable, and the first two
    frozensets are equal (`{1,2} == {2,1}` as sets), so both
    implementations correctly identify the second as a duplicate
    using their respective membership tests. The `set` vs `list`
    backing of `seen` does not matter when elements are hashable
    and equality is well-behaved.

INPUT 3: [[1, 2], [1, 2], [3]]
  - Implementation A → raises `TypeError: unhashable type: 'list'`
    on the very first iteration when it tries `seen.add([1, 2])`
    (verified, /tmp/peep_results3.txt). No items are yielded; the
    exception propagates out of the generator on the first `next()` call.
  - Implementation B → [[1, 2], [3]]   (verified)
  - DISAGREE.
    Mechanism: HASHABILITY. `set.add` requires `obj.__hash__` to return
    an int; lists override `__hash__ = None`, so any list raises
    TypeError when used as a set element. `list.__contains__` only
    uses `__eq__`, which lists do define (element-wise). This is the
    canonical hashable-vs-equality-only distinction.
    (See trace-table rows for `set.__contains__` and `list.__contains__`,
    and SP2.)

INPUT 4: infinite generator yielding 0,1,0,1,0,1,...
         caller breaks after collecting 4 items.
  - Implementation A → yields 0, then 1, then BLOCKS FOREVER inside the
    generator's inner `for item in iterable` loop. The caller collects
    [0, 1] and then `next()` never returns. The caller's "break after 4"
    condition is never evaluated a 3rd time because `next()` does not
    return. (Verified by simulating with 1000-item bounded input and
    asking for 4 outputs: A yields only [0, 1], consuming the full input
    without yielding a third — /tmp/peep_results3.txt. On a truly
    infinite source, this becomes an infinite loop.)
  - Implementation B → identical observable behavior: yields 0, then 1,
    then blocks forever for the same reason. Caller collects [0, 1] and
    hangs on the third `next()`. (Same verification.)
  - AGREE on observable output prefix [0, 1]; AGREE on hang. There is
    NO observable difference in produced items, and no difference in
    the "break after 4" outcome (neither reaches 4).
    Underlying mechanism (per SP4): the cardinality of distinct values
    in the input (= 2) bounds the number of items either generator can
    EVER yield. Once that prefix is exhausted, both generators settle
    into an infinite skip loop.
    There is a latent NON-observable performance difference (per SP5):
    A's per-item check is O(1), B's is O(k=2). Both are constant here,
    so it is undetectable from the outside.

SUMMARY OF DISAGREEMENTS AND THEIR MECHANISMS
  - Input 1: AGREE.
  - Input 2: AGREE — frozensets are hashable; equality and hash are
    consistent for sets (order-insensitive equality + matching hash).
  - Input 3: DISAGREE.
    Mechanism: HASHABILITY (`list.__hash__ is None` → `set.add(list)`
    raises TypeError; `list.__contains__` only requires `__eq__`).
  - Input 4: AGREE on output and on hang.
    No observable disagreement. (Latent: asymptotic complexity of
    membership test — set O(1) vs list O(k) — but k stays at 2.)
```

---

## Per-input answers (plain summary)

**Input 1 — `[1, 2, 1, 3, 2]`:**
  A → `[1, 2, 3]`. B → `[1, 2, 3]`. **Agree.**

**Input 2 — `[frozenset({1,2}), frozenset({2,1}), frozenset({3,4})]`:**
  A → `[frozenset({1, 2}), frozenset({3, 4})]`. B → same. **Agree.** Frozensets are hashable, and `frozenset({1,2}) == frozenset({2,1})` (verified), so both implementations recognise the second element as a duplicate. The hash/eq contract holds, so both `set.__contains__` and `list.__contains__` agree.

**Input 3 — `[[1, 2], [1, 2], [3]]`:**
  A → **raises `TypeError: unhashable type: 'list'`** on the first `next()` (when it tries `seen.add([1, 2])`); no items are yielded. B → `[[1, 2], [3]]` with no error. **Disagree.** The mechanism is **hashability**: `list.__hash__` is `None`, so lists cannot go into a `set`, but `list.__contains__` only requires `__eq__`, and lists define element-wise equality.

**Input 4 — infinite `0, 1, 0, 1, ...`, caller breaks after collecting 4 items:**
  A → caller receives 0, then 1, then `next()` blocks forever. The "collect 4" target is never reached. B → identical behavior: 0, 1, then hang. **Agree on observable output (both produce the prefix `[0, 1]`) and on the hang.** The underlying reason is that the input has only 2 distinct values, so neither generator can ever yield a third — once both unique values are seen, the inner `for` loop consumes the infinite stream forever without ever taking the `if item not in seen:` branch. There is a *latent* asymptotic-complexity difference (set membership O(1) vs list membership O(k)), but with k = 2 it is not observable.

**Disagreements and their mechanisms:**
  - Input 3 only. Mechanism: **hashability** — `set` requires `__hash__`; `list.__contains__` does not. Lists set `__hash__ = None`, so they cannot be added to a set; using a list as the `seen` container sidesteps the requirement.
  - (Input 4 has a latent **asymptotic complexity** difference — set O(1) membership vs list O(k) membership — but it is not observable here because k stays at 2 and the dominant effect is the infinite skip loop common to both.)
