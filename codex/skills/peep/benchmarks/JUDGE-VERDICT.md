# Peep v2 Kaizen Benchmark — Hephaestus Verdict

## Summary
- Net score: +1
- Consistent outperformance: No
- Recommendation: ITERATE

## Benchmark 1 — patch-equivalence

**Correct answer:** Yes, Patch A and Patch B are equivalent modulo the listed test suite. For `"alice2024"`, `"12345"`, `99`, and `"@bob"`, both patches produce the same expected string and no listed test distinguishes them. They are not equivalent for all possible Python inputs: for example, `True` and negative integers distinguish them, but those inputs are outside the existing suite.

**with_skill verdict:** Reaches the correct answer. It traces all four tests correctly, including the important legacy `int` path where Patch A prefixes via `isinstance(name, int)` and Patch B prefixes after `str(99)`. It also properly quarantines latent divergences such as `bool` and arbitrary non-str/non-int values as out-of-suite behavior.

**baseline verdict:** Reaches the correct answer. It traces every listed test correctly and also identifies real out-of-suite divergences, including `bool` and negative integer usernames. It is shorter, but not materially less correct or complete on the asked modulo-tests question.

**Winner:** tie

**Discriminating finding:** None; both outputs contain the key reasoning step that `test_welcome_int_username_legacy` does not distinguish the patches because Patch A's f-string and Patch B's `str()` coercion both yield `"@99"`.

**Surface artifact penalty:** The with_skill certificate is much longer, but the extra structure does not add a decisive insight over the baseline.

## Benchmark 2 — fault-localization

**Correct answer:** The defective code region is `src/promo.py`, specifically the `_applied` state and the short-circuit in `PercentOff.apply`: after one call on the same `PercentOff` instance, later calls return the amount unchanged, so `Invoice.total()` is non-idempotent and can return `25.0` instead of `22.5`. However, strict ground truth from only the shown test is awkward: `invoice.apply_promo(PercentOff(percent=10))` constructs a fresh instance inline, so the exact test as shown cannot fail intermittently from prior state unless there is additional hidden sharing, monkeypatching, fixture reuse, or another call to `total()` not shown in the prompt. The right answer should therefore identify `src/promo.py: self._applied` / `if self._applied: return amount` as the bug while flagging the hidden-state assumption behind the `~1 in 8` xdist explanation.

**with_skill verdict:** Partially reaches the correct answer and is the stronger of the two. It correctly localizes the mechanism to `src/promo.py:6-10`, especially the `if self._applied: return amount` gate, and explains why the exact wrong value `25.0` means the discount path was skipped. Its best insight is that `Invoice.total()` becomes non-idempotent because it delegates to a stateful `promo.apply`. Weakness: it overstates the xdist/shared-instance story as confirmed even though the prompt's failing test constructs a fresh `PercentOff` inline; that assumption should have been marked as unverified rather than treated as the explanation.

**baseline verdict:** Also partially reaches the correct answer. It correctly names mutable `_applied` state as the root cause and explicitly says the test as written should not observe `_applied == True` on its own, which is an important caveat. But it invents unusable line numbers (`src/promo.py:43`, `46-48`) that do not correspond to the provided snippet, and it still leans on an unproven shared-instance explanation for the xdist failure.

**Winner:** with_skill

**Discriminating finding:** with_skill identifies the actual snippet-level fault as `src/promo.py:7` / `src/promo.py:6-10` and traces `total()` becoming non-idempotent, while the baseline's cited line numbers are fabricated relative to the prompt.

**Surface artifact penalty:** None for the win; the extra structure surfaced a better call-stack trace, though both answers should have been more skeptical about the hidden xdist mechanism.

## Benchmark 3 — code-qa

**Correct answer:** For input 1, both yield `[1, 2, 3]`. For input 2, treating the elements as `frozenset`, both yield the first `{1,2}` frozenset and `{3,4}` because equal frozensets are hashable and compare equal. For input 3, Implementation A raises `TypeError: unhashable type: 'list'` before yielding useful output, while Implementation B yields `[[1, 2], [3]]`; the mechanism is hashability versus equality-only list membership. For input 4, both yield `0`, then `1`, then hang forever waiting for a third novel item; the caller never reaches the “break after 4” condition. The set/list asymptotic difference is real in general but not an observable output difference for the alternating `0,1` stream because the number of distinct values is bounded at two.

**with_skill verdict:** Reaches the correct answer. It gets all four input cases right, distinguishes hashability from equality, rejects the frozenset trap, and correctly describes the infinite-stream behavior as `[0, 1]` followed by a hang. It is slightly imprecise in one summary sentence that says A fails “when it tries `seen.add([1, 2])`”; the first hash failure can occur during `item not in seen`, but the overall diagnosis is still correct.

**baseline verdict:** Reaches the correct answer. It gives the same per-input results and is especially clear that list membership uses `==`, not identity, and that the asymptotic difference is latent rather than output-distinguishing for the specific infinite stream. Its summary table's “No on asymptotic cost” wording is a little loose, but the surrounding explanation correctly says both hang with the same yielded prefix.

**Winner:** tie

**Discriminating finding:** None decisive; both outputs contain the key insight that input 4 does not produce four items at all, because after `0` and `1` every upstream value is already in `seen` and neither generator yields again.

**Surface artifact penalty:** The with_skill answer is much longer but not materially more correct than the baseline.

## Benchmark 4 — brownfield-construction

**Correct answer:** The plan should modify `src/clients/bar.py` and `tests/clients/test_bar_client.py` only. It should reuse `src/util/retry.py::with_retry` because that helper is explicitly canonical and exponential, and it should not use or expand `legacy_retry.py`. It should retry `get_gadget` and `list_gadgets` on connection/timeout errors and true 5xx responses, not on 4xx responses, preserve the public `BarClient` method signatures, leave `__init__` untouched, update the existing happy-path test to set `status_code = 200`, and patch `src.util.retry.time.sleep` in retry tests so tests do not actually sleep.

**with_skill verdict:** Reaches the correct answer and is materially better. It chooses the canonical `with_retry`, rejects `retry_legacy` for the right project-history reason, narrows 5xx handling with a `TransientHTTPError`, preserves 4xx immediate failure, covers both BarClient methods, and explicitly catches the subtle test gotcha that sleep must be patched at `src.util.retry.time.sleep`. It also notes the MagicMock comparison issue in the existing test and proposes the minimal `status_code = 200` update.

**baseline verdict:** Mostly reaches the correct answer. It also reuses `with_retry`, rejects `legacy_retry`, gives a concrete helper design, and lists the right core tests. Weaknesses: it uses `resp.status_code >= 500` rather than the more precise `500 <= status_code < 600`, and its test guidance says to patch `src.clients.bar.time.sleep` “or” `src.util.retry.time.sleep`, even though `time` is imported in `src.util.retry` and the former target will not exist under its proposed `bar.py`.

**Winner:** with_skill

**Discriminating finding:** with_skill explicitly identifies the sleep-patch path gotcha as `src.util.retry.time.sleep`, while baseline offers `src.clients.bar.time.sleep` as an option even though `bar.py` does not import `time`.

**Surface artifact penalty:** None; with_skill wins on substantive brownfield integration details, not on certificate theatre.

## Benchmark 5 — greenfield-construction

**Correct answer:** A strong plan should choose Python stdlib `csv` + `json`, avoid runtime dependencies, package a console script named `csv2jsonl`, stream stdin to stdout row-by-row, use the header row as keys, test quoted commas and JSONL shape, and give fresh-clone commands such as creating a venv, installing editable with test extras, running `pytest`, and manually piping CSV through `csv2jsonl`. It should explicitly reject heavy dependencies like pandas/polars and avoid adding flags or abstractions not requested.

**with_skill verdict:** Reaches the broad architecture but is weaker in practical implementability. It correctly chooses zero runtime dependencies, a package with a console entry point, pytest as a dev dependency, streaming, and tests for quoted commas and JSONL shape. But it has concrete inaccuracies: it says the “first non-empty row” is the header even though the spec says the header row, and it claims Python `csv.DictReader` defaults make extra cells dropped and missing cells empty strings, which is not true (`DictReader` defaults use `restkey=None` for extra cells and `restval=None` for missing cells). It also spends many lines certifying sufficiency without giving as concrete an implementation skeleton as the baseline.

**baseline verdict:** Reaches the correct answer and is more implementable. It gives a clear file tree, a concise `__main__.py`/`convert()` skeleton, zero runtime dependencies, explicit rejection of pandas/click/orjson, a richer but still relevant test list, and exact fresh-clone commands plus expected smoke-test output. It does add some arguably extra behavior (BOM stripping, broken-pipe handling, ragged-row policy), but those are flagged as design choices rather than smuggled in as requirements, and the core plan remains simple.

**Winner:** baseline

**Discriminating finding:** baseline provides a concrete streaming implementation skeleton using `csv.DictReader(..., restkey="_extra")` and `json.dumps(..., ensure_ascii=False)`, while with_skill misstates `DictReader`'s default ragged-row behavior.

**Surface artifact penalty:** Yes. with_skill's certificate gives an appearance of rigor, but the baseline's shorter practical plan is more accurate and more directly handoff-ready.

## Overall Reasoning

with_skill did not consistently outperform baseline: it tied on patch-equivalence and code-QA, won on fault-localization and brownfield-construction, but lost the greenfield-construction benchmark. The strongest evidence for the skill is Benchmark 4, where the certificate forced project-respecting details that matter in a brownfield plan: choosing the canonical helper, preserving 4xx behavior, updating the MagicMock status code, and patching `src.util.retry.time.sleep`. The weakest evidence is Benchmark 5, where the certificate produced confident but wrong statements about `csv.DictReader` defaults and a subtle deviation from “header row” to “first non-empty row.”

Recommendation: ITERATE. The skill is promising, especially for brownfield integration and line-by-line reasoning, but it does not clear the kaizen bar yet because one regression is meaningful. The templates needing work are greenfield-construction and, secondarily, fault-localization. Greenfield needs a “stdlib/API semantics check” step before certifying assumptions, so the agent verifies things like `DictReader` defaults instead of writing plausible but false behavior. Fault-localization needs a stricter “does the shown failing test actually reach this state?” gate, so hidden xdist/shared-fixture explanations remain hypotheses unless the prompt provides evidence for shared objects or test pollution.
