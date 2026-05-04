# Behavioral comparison of `unique_in_order` Implementations A and B

Both implementations are generators that yield each element on its first appearance, in input order. The only differences are the data structure backing `seen` (set vs list) and how membership is tested (`hash + ==` vs linear `==` scan). Those differences in mechanism produce four distinct categories of observable consequence: hashability requirements, equality vs identity, asymptotic complexity, and behavior on infinite streams. The four inputs below each probe one of these.

All output below was produced by literally running the two functions in CPython 3.12.3.

---

## Input 1: `[1, 2, 1, 3, 2]`

Implementation A output:
```
[1, 2, 3]
```

Implementation B output:
```
[1, 2, 3]
```

**Agreement: yes (identical output).**

`int` is hashable and equality on ints is the obvious mathematical equality. Both `set` and `list` correctly identify `1` and `2` as already-seen on their second occurrence. The two implementations are observably indistinguishable on this input.

(There is a hidden non-observable difference: A's per-element membership test is amortized O(1); B's is O(k) in the number of unique items seen so far. On a 5-element input this is invisible.)

---

## Input 2: `[frozenset({1, 2}), frozenset({2, 1}), frozenset({3, 4})]`

Implementation A output:
```
[frozenset({1, 2}), frozenset({3, 4})]
```

Implementation B output:
```
[frozenset({1, 2}), frozenset({3, 4})]
```

**Agreement: yes (identical output).**

`frozenset({1, 2}) == frozenset({2, 1})` is `True` and, crucially, `hash(frozenset({1, 2})) == hash(frozenset({2, 1}))`. Frozensets satisfy the hash/equality contract: equal objects must have equal hashes. So:

- A's `set`-based `seen` correctly bucket-collides the second frozenset against the first and detects equality. The second item is recognized as a duplicate.
- B's `list`-based `seen` walks the list comparing with `==`, which also reports equality. The second item is recognized as a duplicate.

Both yield the first frozenset and the third one, and skip the second. Note this is *only* true because the input is `frozenset` (the prompt's stipulation). With plain `set`, A would raise `TypeError: unhashable type: 'set'` while B would still work, because `set` defines `__eq__` but not `__hash__` — that is exactly the hashability axis that input 3 below exposes for `list`.

---

## Input 3: `[[1, 2], [1, 2], [3]]`

Implementation A output:
```
TypeError: unhashable type: 'list'
```

Implementation B output:
```
[[1, 2], [3]]
```

**Disagreement.**

Underlying mechanism: **hashability**. `list` is mutable and intentionally has no `__hash__`. The very first call to `item not in seen` inside A triggers a hash of `[1, 2]` to look it up in the set, which raises `TypeError`. The generator dies on the first element — A never yields anything; the exception is raised the first time the caller advances the generator (i.e., during `list(...)`, on the first `next` call).

B's `seen` is a `list`, so `item not in seen` performs a linear scan using `==`. Equality on lists is element-wise, so the second `[1, 2]` is recognized as equal to the first and skipped. B returns `[[1, 2], [3]]` with no error.

Note this also illustrates **equality, not identity**: the two `[1, 2]` literals are distinct objects (`is` would return `False`), but `==` returns `True`, and B uses `==`. If B had used `is`-based membership it would have yielded `[[1, 2], [1, 2], [3]]`. Python's `in` operator for lists uses `==` (with an `is`-shortcut as an optimization), so B treats them as duplicates. Identity vs equality is the second axis on which the two implementations could in principle diverge — they happen to behave the same here only because `set` lookup also uses `==` after a hash match — but that comparison is gated by hashability, which is what kills A.

---

## Input 4: An infinite generator yielding `0, 1, 0, 1, 0, 1, ...`, caller `break`s after collecting 4 items.

Implementation A output:
```
(hangs forever; never produces a 4th item, so the caller's `break` is never reached)
```

Implementation B output:
```
(hangs forever; same reason)
```

**Agreement on the user-visible result: both hang. But the asymptotic cost while hanging differs.**

After the first two iterations both generators have yielded `0` and `1`. From the third underlying-iterator element onward, every value is a member of `seen`, so the inner `if` is always false and **neither generator ever yields again**. The caller's `for` loop is suspended waiting for a value that never comes; the `if len(...) >= 4: break` test is never evaluated because control never returns to the caller body. Both implementations "produce" exactly two items and then loop forever consuming the upstream iterator.

The two are observationally equivalent in *what* they yield (nothing more, forever), but they differ in **asymptotic cost while not yielding**:

- A's `item not in seen` against a 2-element `set` is O(1) per upstream element, so A churns through the infinite stream at O(n) total work for n consumed elements — at constant cost per element regardless of how many uniques have been seen.
- B's `item not in seen` against a 2-element `list` is O(k) where k is the number of uniques. Here k = 2, so it is also constant-per-element (just a slightly larger constant).

So in this specific input the asymptotic gap is invisible (k is bounded at 2). But this is the input that *would* expose the third axis — asymptotic complexity — if the stream contained a growing number of distinct values. For example, on an infinite stream of fresh integers `0, 1, 2, 3, ...` after consuming n elements A would have done O(n) work and B would have done O(n^2) work, with B becoming dramatically slower over time. That difference in complexity is observable as wall-clock time, even though both produce the same output sequence.

A secondary, very subtle difference also lives on this axis: A's `seen` set retains hashes and may reallocate/rehash as it grows; B's `seen` list grows by amortized doubling. Neither matters for the 0/1 stream.

---

## Summary table

| Input | A | B | Agree? | Mechanism that matters |
|------|---|---|--------|------------------------|
| 1. `[1, 2, 1, 3, 2]` | `[1, 2, 3]` | `[1, 2, 3]` | Yes | (hashable + cheap equality; nothing diverges) |
| 2. `[frozenset({1,2}), frozenset({2,1}), frozenset({3,4})]` | `[frozenset({1,2}), frozenset({3,4})]` | `[frozenset({1,2}), frozenset({3,4})]` | Yes | Hash/equality contract holds for frozenset, so set and list lookups give the same answer. (Would diverge for plain `set` — A would TypeError.) |
| 3. `[[1,2], [1,2], [3]]` | `TypeError: unhashable type: 'list'` | `[[1,2], [3]]` | **No** | **Hashability**: lists have no `__hash__`, so A's `set` membership fails immediately; B's linear scan uses `==` and works. |
| 4. infinite `0,1,0,1,...`, break after 4 | Hangs (only 2 unique items ever exist) | Hangs (same reason) | Yes on output, **No on asymptotic cost** | **Asymptotic complexity**: A is O(1) per upstream element, B is O(k). Equal here (k=2) but B degrades to O(n^2) total on streams with growing uniqueness. |

## The three underlying language mechanisms in play

1. **Hashability** (input 3, and would-be input 2 with plain `set`). A requires its elements to be hashable because `set` is a hash table; B does not. Mutable container types — `list`, `set`, `dict` — are deliberately not hashable, so A cannot consume them at all.

2. **Equality vs identity**. Both `set` and `list` membership in Python use `==` (with an `is`-check as a fast path). The two implementations agree on this axis — but only because Python's `in` operator on a `list` uses `==`, not `is`. If B had been written with an explicit `any(x is item for x in seen)` it would have differed from A on input 3.

3. **Asymptotic complexity** (input 4 and any large input with many unique elements). A is O(n) total; B is O(n × k) where k is the number of distinct items seen. On bounded-uniqueness inputs (like the 0/1 stream) this is invisible; on growing-uniqueness inputs it is the dominant practical difference.
