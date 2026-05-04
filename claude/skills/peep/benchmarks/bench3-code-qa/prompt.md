In Python, what is the difference in observable behavior between these two implementations of `unique_in_order`? Both take an iterable and yield each element only the first time it appears, preserving order.

IMPLEMENTATION A:
```python
def unique_in_order(iterable):
    seen = set()
    for item in iterable:
        if item not in seen:
            seen.add(item)
            yield item
```

IMPLEMENTATION B:
```python
def unique_in_order(iterable):
    seen = []
    for item in iterable:
        if item not in seen:
            seen.append(item)
            yield item
```

For each of the following inputs, state precisely what Implementation A does, what Implementation B does, and whether they agree:

1. `[1, 2, 1, 3, 2]`
2. `[{1, 2}, {2, 1}, {3, 4}]` (a list of frozen sets — assume frozenset, not set)
3. `[[1, 2], [1, 2], [3]]` (a list of lists)
4. An infinite generator that yields `0, 1, 0, 1, 0, 1, ...` and the caller breaks after collecting 4 items.

For each disagreement, identify the underlying language mechanism that causes it (e.g. hashability, identity vs equality, asymptotic complexity).
