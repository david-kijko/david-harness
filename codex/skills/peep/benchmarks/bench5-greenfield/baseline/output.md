# Plan: `csv2jsonl` CLI

## 1. Restating the problem (so the implementer can sanity-check me)

Build a CLI named `csv2jsonl` that:

- Reads CSV from **stdin**.
- Writes **JSON Lines** (one JSON object per line, `\n`-terminated, UTF-8) to **stdout**.
- Uses the **first row as header**; every subsequent row becomes one JSON object whose keys are header names and whose values are the row's cells (as strings).
- Correctly handles **quoted fields containing commas** (and, by implication, quoted fields containing quotes and newlines — that's the same RFC 4180 rule).
- Is invokable as `csv2jsonl < input.csv > output.jsonl`.
- Python is acceptable.

That's the entire spec. Anything beyond it is speculative.

## 2. What I considered and rejected

I want to be explicit about the design space because the spec is intentionally thin and the user will not answer follow-ups.

### Language

- **Python (chosen).** The spec explicitly blesses it. The standard library's `csv` module already implements RFC 4180 quoting (including embedded commas, embedded quotes via `""`, and embedded newlines inside quoted fields). `json` is also stdlib. Zero dependencies. Works on a laptop and in a slim container.
- **Rust / Go.** Faster, single static binary, better for "called millions of times" or "huge files." Rejected because (a) the spec doesn't hint at scale, (b) it adds a toolchain the user didn't ask for, and (c) Python with `csv.DictReader` streaming row-by-row is already O(1) memory and plenty fast for the obvious use cases. If the user later says "this needs to chew 50 GB at line rate," we revisit.
- **Bash + `jq`.** `jq` has a `@csv` decoder but RFC 4180 quoting in pure bash is a footgun. Rejected.

### Dependencies

- **`pandas`.** Rejected. Heavy, slow to import (~1s cold), loads everything into memory, mangles types (turns `"01"` into `1`, empty cells into `NaN`, etc.). The spec says "use the header row as keys" and says nothing about type inference — strings-in, strings-out is the safe default.
- **`click` / `typer` / `argparse`.** The tool takes **no arguments**. It's pure stdin -> stdout. No flags means no argument parser. Rejected (even `argparse` is overkill here, though I'd accept it if the implementer prefers a `--help` for discoverability — see §6).
- **`orjson` / `ujson`.** Faster JSON serialization. Rejected — premature optimization with no scale signal.
- **`pytest`.** This is a real choice. See §4.

**Net dependency count: 0 runtime dependencies. 1 dev dependency (`pytest`) — and I'd accept `unittest` instead if the user wants truly zero deps.** I'll go with `pytest` because the test ergonomics are dramatically better and it's a one-line install in a fresh clone.

### Streaming vs. buffering

Stream. `csv.DictReader` over `sys.stdin` plus `json.dumps` per row plus `print` (or `sys.stdout.write`) per row gives constant memory regardless of input size. Costs nothing extra to write and removes a whole class of failure modes.

### JSON encoding choices

- `ensure_ascii=False` so non-ASCII characters in cells round-trip as UTF-8 instead of `\uXXXX` escapes. JSON Lines consumers universally handle UTF-8; escaping bloats output and obscures content.
- No trailing whitespace, no pretty-printing (JSON Lines requires one object per line — pretty-printing would break it).
- Dict key order = header order. `json.dumps` preserves insertion order in Python 3.7+, and `csv.DictReader` yields fields in header order, so this is free.

### Edge cases I'll handle explicitly

- **Empty input** -> exit 0, no output. (No header, no rows.)
- **Header only, no data rows** -> exit 0, no output.
- **A row with fewer cells than the header** -> `csv.DictReader` fills missing keys with `None`. I'll let it serialize as JSON `null`. (Alternative: empty string. I think `null` is more honest about "this cell wasn't there," and it's the stdlib default. Documenting it is enough.)
- **A row with more cells than the header** -> `csv.DictReader` puts extras under the key `None`, which `json.dumps` will refuse. I'll set `restkey="_extra"` so extras land in a list under the key `"_extra"` rather than crashing. Documented in the README.
- **Embedded newlines in quoted fields** -> the stdlib `csv` module handles them. Tested.
- **BOM at start of file** -> open stdin as `utf-8-sig` so a leading BOM is stripped from the first header name. Otherwise the first key becomes `"﻿name"` and every downstream consumer breaks subtly.
- **Broken pipe** (e.g. `csv2jsonl < big.csv | head`) -> catch `BrokenPipeError`, exit cleanly with status 0. Otherwise Python prints an ugly traceback.

### Edge cases I'll *not* handle (and will say so)

- Type inference (numbers, booleans, nulls). Spec says strings-as-keys, says nothing about value types. Strings out.
- Custom delimiters (TSV, semicolon). Not in spec. Easy to add later as `--delimiter` if asked.
- Encodings other than UTF-8 (with optional BOM). Not in spec.
- Skipping comment lines, multi-line headers, etc. Not in spec.

## 3. Files I would create

Project root: an empty directory. After this plan, the tree is:

```
csv2jsonl/
├── README.md
├── pyproject.toml
├── src/
│   └── csv2jsonl/
│       ├── __init__.py
│       └── __main__.py        # so `python -m csv2jsonl` also works
├── tests/
│   ├── __init__.py
│   └── test_csv2jsonl.py
└── .gitignore
```

File-by-file:

### `pyproject.toml`

- Build backend: `setuptools` (stdlib-friendly, no extra install needed beyond `pip`).
- Project metadata: name `csv2jsonl`, version `0.1.0`, Python `>=3.9` (covers every supported CPython; gives us `dict` ordering guarantees and modern `csv` behavior).
- `[project.scripts]` entry point: `csv2jsonl = "csv2jsonl.__main__:main"`. This is what makes `csv2jsonl < input.csv > output.jsonl` work after `pip install`.
- `[project.optional-dependencies]` -> `dev = ["pytest>=7"]`.
- No runtime dependencies.

### `src/csv2jsonl/__init__.py`

- Empty, or one line: `__version__ = "0.1.0"`.

### `src/csv2jsonl/__main__.py`

The whole tool. Roughly 30 lines. Skeleton:

```python
import csv
import io
import json
import sys

def convert(in_stream, out_stream) -> None:
    reader = csv.DictReader(in_stream, restkey="_extra")
    for row in reader:
        out_stream.write(json.dumps(row, ensure_ascii=False))
        out_stream.write("\n")

def main() -> int:
    # Re-open stdin as utf-8-sig to strip a possible BOM, stdout as utf-8.
    stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8-sig", newline="")
    stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", write_through=True)
    try:
        convert(stdin, stdout)
    except BrokenPipeError:
        # Downstream consumer (e.g. `head`) closed the pipe. Not our problem.
        try:
            sys.stdout.close()
        except BrokenPipeError:
            pass
        return 0
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

`newline=""` on stdin is required by the `csv` module so it can see embedded `\r\n` inside quoted fields without the runtime translating them.

### `tests/test_csv2jsonl.py`

See §4 for the test list. Each test calls `convert(io.StringIO(input_csv), io.StringIO())` and asserts on the buffer contents. One end-to-end test shells out via `subprocess` to confirm the installed entry point actually wires up.

### `README.md`

Short. Sections:

1. What it does (one paragraph).
2. Install: `pip install .` (or `pipx install .` for an isolated CLI).
3. Use: `csv2jsonl < input.csv > output.jsonl`.
4. Behavior notes: UTF-8 in/out, BOM stripped, ragged rows -> missing cells become `null`, extra cells go into `"_extra"`, no type inference (everything is a string).
5. Run tests: `pip install -e '.[dev]' && pytest`.

### `.gitignore`

Standard Python: `__pycache__/`, `*.pyc`, `.pytest_cache/`, `dist/`, `build/`, `*.egg-info/`, `.venv/`.

## 4. Tests I would write

All in `tests/test_csv2jsonl.py`. Each one is a few lines; I'd use plain `pytest` functions (no classes).

**Core correctness**

1. `test_basic_two_columns_two_rows` — `a,b\n1,2\n3,4\n` produces exactly two JSON lines with keys `a`, `b`.
2. `test_header_only_no_data` — `a,b\n` produces zero lines of output.
3. `test_empty_input` — `""` produces zero lines of output and exits 0.
4. `test_single_column` — degenerate but common; make sure no off-by-one in the dict construction.

**The headline requirement (quoted fields with embedded commas)**

5. `test_quoted_field_with_embedded_comma` — input row `"hello, world",2` under headers `a,b` -> `{"a": "hello, world", "b": "2"}`. This is the test the spec explicitly demands.
6. `test_quoted_field_with_embedded_quote` — `"she said ""hi""",2` -> value is `she said "hi"`. RFC 4180's other half.
7. `test_quoted_field_with_embedded_newline` — `"line1\nline2",2` -> value contains a real newline; JSON output escapes it as `\n`; still exactly one output line per row.

**Encoding**

8. `test_utf8_passthrough` — non-ASCII header and cell (e.g. `naïve,café`) round-trips without `\uXXXX` escaping.
9. `test_bom_is_stripped_from_first_header` — input starts with `﻿`; first key in output is the clean header, not `"﻿name"`.

**Ragged rows**

10. `test_row_shorter_than_header` — missing cells become JSON `null`.
11. `test_row_longer_than_header` — extras land in `"_extra"` as a list; nothing crashes.

**Output shape**

12. `test_each_row_is_one_line` — output split on `\n` has exactly N+1 elements (N rows + trailing empty string from final newline) and each non-empty element parses as a JSON object.
13. `test_key_order_matches_header_order` — parse the raw output line and assert `list(obj.keys()) == headers`. (Relies on `json` preserving order, which it does.)

**End-to-end (the thing the user will actually do)**

14. `test_cli_entry_point_via_subprocess` — `subprocess.run([sys.executable, "-m", "csv2jsonl"], input=csv_bytes, capture_output=True)` and assert on stdout. Confirms the wiring works without needing the package to be `pip install`-ed first.
15. `test_installed_console_script` *(optional, skipped if the `csv2jsonl` binary is not on PATH)* — same as above but invokes `csv2jsonl` directly. Catches packaging mistakes in `pyproject.toml`'s `[project.scripts]`.

**Robustness**

16. `test_broken_pipe_is_silent` — pipe a large generated CSV into `csv2jsonl` and close the read end early; assert the process exits 0 and prints nothing to stderr. (Easy to write with `subprocess.Popen` and closing `proc.stdout` after one read.)

That's 16 tests, all small. I'd expect the whole suite to run in well under a second.

## 5. Commands a fresh clone would type

Assuming the user just did `git clone <repo> && cd csv2jsonl`:

```bash
# 1. Create and activate a virtualenv (optional but recommended; keeps the
#    dev install from polluting the system Python).
python3 -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate

# 2. Install the package in editable mode plus the dev extra (pytest).
pip install -e '.[dev]'

# 3. Run the test suite.
pytest -q

# 4. Confirm the CLI is wired up. Should print one JSON object per row.
printf 'name,greeting\nAda,"hello, world"\nGrace,hi\n' | csv2jsonl

# 5. The exact invocation from the spec.
printf 'name,greeting\nAda,"hello, world"\nGrace,hi\n' > /tmp/input.csv
csv2jsonl < /tmp/input.csv > /tmp/output.jsonl
cat /tmp/output.jsonl
```

Expected output of step 4 / `cat` in step 5:

```
{"name": "Ada", "greeting": "hello, world"}
{"name": "Grace", "greeting": "hi"}
```

If a user is allergic to virtualenvs and just wants the binary on their PATH:

```bash
pipx install .          # isolated install, `csv2jsonl` available globally
```

If a user wants to avoid installing entirely (one-shot use from a checkout):

```bash
python -m csv2jsonl < input.csv > output.jsonl
```

## 6. Things I'd flag to the user before merging

- **No `--help` / `--version`.** The spec gives no flags, so I added none. Some users will type `csv2jsonl --help` reflexively and get a confusing error (the flag will be parsed as CSV from stdin, which then blocks waiting for input). If we want to be polite, add a 5-line `argparse` shim that exposes only `--help` and `--version` and otherwise passes through. I'd lean toward adding it; it's cheap. Wanted to call it out rather than smuggle it in.
- **`null` vs `""` for missing cells in short rows.** Documented choice; trivial to flip.
- **No type inference.** If downstream consumers expect numbers, they'll have to cast. Deliberate.
- **Python 3.9 floor.** Could go lower (3.7 has the dict-ordering guarantee we rely on), but 3.9 is the oldest non-EOL CPython at this point and saves us from supporting truly ancient runtimes.

If any of those four are wrong, they're each a one-line change.
