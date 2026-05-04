# Hypothesis-Driven Exploration Loop

Use this when a template asks you to *explore* an unfamiliar codebase before filling a section — typically: filling fault-localization's PHASE 2 (code path tracing) when the call chain isn't obvious, or filling brownfield-construction's EXISTING PATTERN SURVEY when you don't yet know what's in the repo.

The loop has roots in Appendix B of Ugare & Chandra (2026) and the more quantitative HypoExplore (2026) which adds explicit confidence thresholds.

## The loop

```
Maintain a hypothesis memory bank: H1, H2, H3, ...
Each hypothesis carries a confidence c ∈ [0, 1] starting at 0.5.

REPEAT until you have enough evidence to fill the template:

  1. State the next hypothesis or pick the lowest-confidence open one:
     HYPOTHESIS H[N]: [what you expect to find and why]
     EVIDENCE EXPECTED: [what you'd grep / read to confirm or refute]
     CONFIDENCE before search: c = [value]

  2. Search:
     ACTION: [grep pattern, file path, or read command]
     RESULT: [what you found, with file:line where applicable]

  3. Update:
     OBSERVATIONS:
       O[N].1: [key fact from the result, with line numbers]
       O[N].2: [another fact]
     UPDATE H[N]: c = [new value]
       if c >= 0.75:  status = CONFIRMED
       if c <= 0.25:  status = REFUTED
       else:          status = REFINED → state the refined hypothesis as H[N+1]

  4. Decide next action:
     UNRESOLVED: [questions still open]
     NEXT ACTION RATIONALE: [why read another file vs commit to template]
```

## Worked example: brownfield pattern survey

Suppose the user asks "add retry with exponential backoff to the Foo client".

```
H1: There is already a retry helper in this repo I should reuse.
EVIDENCE EXPECTED: a file named retry.py / retry.ts / common/retry.* OR
                   a function named retry / with_retry / backoff / exponential_backoff.
CONFIDENCE before: c = 0.5

ACTION: rg -l --iglob '*.py' -e 'def retry|def with_retry|def.*backoff'
RESULT: matches in src/util/retry.py:14, src/clients/legacy_retry.py:42

OBSERVATIONS:
  O1.1: src/util/retry.py:14 defines `with_retry(fn, *, max_attempts, base_delay)`
        — clean signature, used in 8 places (rg shows usages).
  O1.2: src/clients/legacy_retry.py:42 defines `retry_legacy(fn, attempts=3)`
        — only used in src/clients/foo.py:88.
UPDATE H1: c = 0.85 → CONFIRMED (a helper exists)

H2: The helper at src/util/retry.py:14 is the preferred one (vs the legacy one).
EVIDENCE EXPECTED: a comment, deprecation marker, or recent commit favoring one.
CONFIDENCE before: c = 0.6

ACTION: read src/clients/legacy_retry.py header + git log -p src/util/retry.py | head -50
RESULT: legacy_retry.py has comment "# DEPRECATED — use util/retry:with_retry instead. ticket #4421."

OBSERVATIONS:
  O2.1: src/clients/legacy_retry.py:1-3 marks itself deprecated.
  O2.2: util/retry.py was added in commit a3f9b21 with message "extract canonical retry helper".
UPDATE H2: c = 0.95 → CONFIRMED

UNRESOLVED: none for this concern.
NEXT ACTION RATIONALE: enough evidence to fill the survey row.
```

The Existing Pattern Survey row is now defensible:

| Concern | Pattern exists? | Evidence | Still preferred? | Decision |
|---|---|---|---|---|
| retry/backoff | yes (H1 CONFIRMED) | `src/util/retry.py:14` | yes (H2 CONFIRMED); legacy file deprecated `src/clients/legacy_retry.py:1-3` | REUSE `with_retry` |

Note this also surfaces a brownfield gotcha: if you'd only checked H1 and not H2, you might have copied `retry_legacy` (failure mode B2 — deprecated-pattern reuse).

## Worked example: fault localization

Test `test_csv_parsing_with_header` fails with `ParseException`. The test calls `CSVParser.parse(input)`.

```
H1: The bug is in CSVParser.parse() (the directly-invoked method).
CONFIDENCE before: c = 0.6 (default-high because that's where the call lands)

ACTION: read src/csv/parser.py — focus on parse()
RESULT: parse() is 12 lines, mostly delegates to format.with_header(input).

OBSERVATIONS:
  O1.1: parse() at src/csv/parser.py:14 calls self.format.with_header(input).
  O1.2: parse() does no input validation that could raise ParseException.
UPDATE H1: c = 0.2 → REFUTED. The bug is downstream.

H2: The bug is in CSVFormat.with_header() (the immediate callee).
CONFIDENCE before: c = 0.7

ACTION: read src/csv/format.py:with_header
RESULT: with_header at src/csv/format.py:88 — 30 lines, parses header row.
        Line 102 raises ParseException("malformed header") if header has 0 columns.

OBSERVATIONS:
  O2.1: format.py:102 is the only ParseException raise on this path.
  O2.2: line 95 calls header_row.split(',') — does not handle the case where
        header_row is empty.
UPDATE H2: c = 0.9 → CONFIRMED. The empty-header case raises here.

H3: The empty-header case can actually occur from the test input.
CONFIDENCE before: c = 0.6

ACTION: read the test fixture — test_csv_parsing_with_header.csv
RESULT: file starts with "\n" (a leading newline), then real data.

OBSERVATIONS:
  O3.1: leading newline → header_row = "" after split('\n')[0].
  O3.2: split(',') on "" yields [""] (length 1, not 0).
UPDATE H3: c = 0.3 → REFINED.

H4: The bug is in handling header rows that split to ['']  (length 1, not 0).
... (continue)
```

This loop forces you to test each indirection level instead of fixating on the crash site (failure mode F1) or the directly-invoked class (failure mode F2).

## Confidence threshold rationale

The c ≥ 0.75 confirm / c ≤ 0.25 refute thresholds come from HypoExplore (Wang et al., 2026, *Agentic Discovery with Active Hypothesis Exploration*). Two-sided thresholds prevent two failure modes:
- **Premature confirmation** (c ~ 0.6 declared "good enough") — high threshold makes you keep looking.
- **Endless drift** (hypothesis is wrong but never explicitly killed) — low threshold forces you to drop it.

## When NOT to use this loop

Skip the loop when:
- The information you need is already in the prompt (don't ceremoniously "search" for it).
- A single grep would resolve the question — just grep, don't write H1.
- You're filling a template section that already has a structured form (use the template directly).

The loop is for *unfamiliar territory*, not for "everything must be a hypothesis".
