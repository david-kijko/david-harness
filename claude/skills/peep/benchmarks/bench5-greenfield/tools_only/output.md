# Plan: `csv2jsonl` — CSV (stdin) → JSON Lines (stdout)

A written plan for an implementer (or future-me) to build the tool from scratch in a currently-empty directory. **No code is created here**; this is the blueprint.

---

## 1. Re-stating the spec, in my own words

> A CLI named `csv2jsonl`. Reads CSV bytes from `stdin`, writes JSON Lines to `stdout`. The first row is the header; every subsequent row becomes one JSON object whose keys come from the header. Quoted fields with embedded commas must parse correctly. Invocation: `csv2jsonl < input.csv > output.jsonl`. Python is acceptable.

### What the spec does NOT say (and what I am explicitly assuming)

| Question | My default | Why |
|---|---|---|
| All values typed as strings, or coerced to int/float/bool/null? | **Keep as strings.** | The spec says "uses the header row as keys" and says nothing about typing. CSV has no types. Coercion is lossy ("007" ≠ 7) and surprising. If the user wants typing they'll ask. |
| Encoding? | **UTF-8 in, UTF-8 out**, surrogateescape for malformed input bytes so the tool never aborts mid-stream. | JSON Lines mandates UTF-8 (per jsonlines.org / ndjson-spec). |
| Line terminator on output? | **`\n` only** (no `\r\n`), one JSON object per line, trailing `\n` after the last record. | jsonlines.org. |
| Delimiter? | **Comma** (the name says "csv" and the spec example is `input.csv`). No `--delimiter` flag in v1. | YAGNI. Add later if asked. |
| What about an empty file / header-only file / blank lines? | Empty input → empty output, exit 0. Header-only → exit 0, no rows. Blank lines mid-stream are skipped by `csv.reader` naturally only when they're truly empty; we'll make the policy explicit (see §6). | Robust defaults. |
| Rows with too few/too many fields vs. header? | **Too few:** missing keys get `null` (DictReader behavior with `restval=None`). **Too many:** extras are collected under key `null` by default — we'll instead raise to stderr with row number and exit non-zero, because silently dropping data is worse than failing loudly. | Loud-fail on shape mismatch is the safer default for a one-shot tool. |
| Huge files? | **Stream row-by-row**, never load whole file. `csv.DictReader` + `json.dumps` per row is already O(1) memory. | Spec doesn't promise huge files but streaming costs us nothing and protects us. |
| `BrokenPipeError` (e.g. `csv2jsonl < big.csv | head`)? | Catch and exit 0. | Standard Unix-tool behavior. |

If any of the above defaults are wrong, I'd want the user to push back **before** I build. None of them are tied to the wording of the spec.

---

## 2. What I considered and rejected

1. **A bash one-liner with `jq`.** Rejected: `jq` cannot parse RFC 4180 quoted CSV (embedded commas, doubled-quote escapes). The spec explicitly calls out quoted fields, so jq would silently mis-parse.
2. **Pandas (`pd.read_csv` → `to_json(orient='records', lines=True)`).** Rejected: 50 MB dependency, multi-second import time, eagerly loads frame into memory, and coerces types in ways the spec did not ask for. Massive overkill for a 30-line tool.
3. **Third-party CSV libs (`python-csv`, `csvkit`, `clevercsv`).** Rejected: stdlib `csv` already implements the excel dialect (RFC-4180-style quoting, doubled-quote escape, embedded commas). Confirmed against [docs.python.org/3/library/csv.html](https://docs.python.org/3/library/csv.html) and [CPython Lib/csv.py](https://github.com/python/cpython/blob/main/Lib/csv.py). Adding a dep here buys nothing.
4. **`orjson` / `ujson` for output.** Rejected for v1: stdlib `json` is fast enough for a stdin-bound tool, and zero deps means a fresh clone runs immediately with `python3` only. Revisit only if a benchmark shows json.dumps is the bottleneck.
5. **Click / Typer / argparse.** Rejected for v1 — there are *zero* CLI flags in the spec. `sys.argv` only needs to recognize `--help`/`-h` and `--version`. We can do that in 5 lines with `argparse` (stdlib) and avoid adding any framework.
6. **A type-coercion mode (`--infer-types`).** Rejected: not asked for. Adding flexibility nobody requested is the #1 way to make a 50-line tool become a 500-line tool.
7. **Reading files by path as positional args.** Rejected: spec explicitly says `< input.csv`. Stdin-only keeps the contract small. Users who want file input use the shell.

### Will I add ANY runtime dependency?

**No.** Pure Python 3 stdlib (`csv`, `json`, `sys`, `argparse`, `io`). Test-only deps go in `[project.optional-dependencies].dev`.

---

## 3. Files I would create

Working in the empty directory `csv2jsonl/`:

```
csv2jsonl/
├── pyproject.toml          # PEP 621 metadata + console script entry point + dev deps
├── README.md               # 30-line usage doc, examples, install
├── LICENSE                 # MIT
├── .gitignore              # standard Python
├── .python-version         # 3.9 (lowest I'll support)
├── src/
│   └── csv2jsonl/
│       ├── __init__.py     # __version__ = "0.1.0"
│       ├── __main__.py     # `python -m csv2jsonl` → main()
│       └── cli.py          # the actual tool: ~40 LOC
└── tests/
    ├── __init__.py
    ├── conftest.py         # shared fixtures (tmp paths, sample CSVs)
    ├── test_cli.py         # end-to-end behavior via subprocess
    ├── test_parsing.py     # unit tests for the row→dict transform
    └── data/               # fixture CSVs (committed, small)
        ├── simple.csv
        ├── quoted_commas.csv
        ├── quoted_quotes.csv
        ├── crlf.csv
        ├── utf8_bom.csv
        ├── empty.csv
        ├── header_only.csv
        ├── ragged_short.csv
        ├── ragged_long.csv
        └── blank_lines.csv
```

### File-by-file purpose

- **`pyproject.toml`** — `[project]` block with name, version, description, `requires-python = ">=3.9"`, `dependencies = []`, `[project.scripts] csv2jsonl = "csv2jsonl.cli:main"` (per [PEP 621](https://peps.python.org/pep-0621/) / [packaging.python.org/specifications/entry-points](https://packaging.python.org/specifications/entry-points/)). Build backend = `hatchling` (simpler than setuptools, no `setup.py` boilerplate). `[project.optional-dependencies] dev = ["pytest>=7", "ruff"]`.
- **`src/csv2jsonl/cli.py`** — the whole tool. Sketch:
  ```
  def main(argv=None) -> int:
      parse --help / --version with argparse
      open sys.stdin.buffer wrapped as TextIOWrapper(encoding="utf-8",
          errors="surrogateescape", newline="")     # newline="" is required by csv module
      open sys.stdout wrapped same, newline="\n"
      reader = csv.DictReader(in_stream)
      validate header is non-empty; else exit 0 cleanly
      for i, row in enumerate(reader, start=2):     # start=2 because header was line 1
          if extra fields detected (key None in row dict): die loudly with row number
          out.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
      handle BrokenPipeError → return 0
      return 0
  ```
- **`__main__.py`** — `from .cli import main; raise SystemExit(main())`. Lets users do `python -m csv2jsonl` even before pip-installing the entry point.
- **`README.md`** — 4 sections: Install (`pipx install csv2jsonl` once published, or `pip install -e .` for dev), Usage (one example block), Behavior (bullet list of the assumptions in §1), Limitations.
- **`tests/conftest.py`** — `pytest` fixtures returning paths to `tests/data/*.csv`, plus a `run_cli(stdin_bytes)` helper that invokes the installed entry point via `subprocess.run([sys.executable, "-m", "csv2jsonl"], input=..., capture_output=True)`.

---

## 4. Tests I would write

The spec has exactly four observable claims; everything else is behavior I'm choosing. Tests must cover all four claims, plus my chosen edge-case policies.

### Spec-mandated tests (these MUST pass)

1. **`test_basic_roundtrip`** — `a,b,c\n1,2,3\n4,5,6\n` → `{"a":"1","b":"2","c":"3"}\n{"a":"4","b":"5","c":"6"}\n`. Exact byte equality on stdout.
2. **`test_header_becomes_keys`** — header `name,age` produces objects with exactly those keys, in any (insertion) order.
3. **`test_quoted_field_with_embedded_comma`** — `name,note\n"Smith, John","hello, world"\n` → `{"name":"Smith, John","note":"hello, world"}`. **This is the spec's headline requirement** — must be a hard assertion.
4. **`test_invokable_as_csv2jsonl_redirect`** — after `pip install -e .`, run `bash -c 'csv2jsonl < tests/data/simple.csv > /tmp/out.jsonl'`, assert exit 0 and file contents match expected.

### My-policy tests (defending the choices in §1)

5. **`test_doubled_quote_escape`** — `q\n"He said ""hi"""\n` → `{"q":"He said \"hi\""}`. Standard RFC 4180 escape.
6. **`test_crlf_input`** — same input as test 1 but with `\r\n` line endings → identical output. (Requires opening stdin with `newline=""`.)
7. **`test_unicode_passthrough`** — `name\nJürgen\n你好\n` → JSON contains the literal UTF-8 chars (`ensure_ascii=False`), not `ü` escapes. Stdout decoded as UTF-8 must equal `{"name":"Jürgen"}\n{"name":"你好"}\n`.
8. **`test_utf8_bom_stripped`** — input begins with `﻿`; the BOM must not appear inside the first column name. (Open stdin with `encoding="utf-8-sig"`? Or detect-and-strip? Decision: use `utf-8-sig` for input — it's a no-op when no BOM is present.)
9. **`test_empty_input_exits_zero_no_output`**.
10. **`test_header_only_exits_zero_no_output`**.
11. **`test_blank_line_in_middle`** — DictReader by default emits a row of `{key: None, ...}` for a blank line; we will skip rows where every value is empty/None. Test asserts that.
12. **`test_ragged_short_row_fills_missing_with_null`** — `a,b,c\n1,2\n` → `{"a":"1","b":"2","c":null}`.
13. **`test_ragged_long_row_fails_loudly`** — `a,b\n1,2,3\n` → exit code != 0, stderr mentions "row 2" and "extra field".
14. **`test_broken_pipe_clean_exit`** — pipe stdout to `head -n 0` equivalent, assert exit 0 and no traceback on stderr.
15. **`test_large_input_streams`** — generate 100k synthetic rows, pipe through, assert peak RSS stays under (say) 50 MB and output line count is correct. Marked `@pytest.mark.slow` so it's opt-in.
16. **`test_help_and_version`** — `csv2jsonl --help` exits 0 and mentions "stdin"/"stdout"; `csv2jsonl --version` prints `0.1.0`.

### What I deliberately do NOT test

- Type inference (we don't do it).
- Custom delimiters / quote chars (no flags).
- Reading from file paths (stdin-only by design).

---

## 5. Commands a fresh clone would type

Assuming the user just did `git clone <url> && cd csv2jsonl`:

```bash
# 1. Create + activate a venv (no global pollution)
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. Editable install + dev tools (one line, pulls pytest/ruff from PyPI)
pip install -e '.[dev]'

# 3. Run the test suite
pytest -q                          # fast tests only
pytest -q -m slow                  # opt-in: the 100k-row streaming test

# 4. Lint (optional but cheap)
ruff check src tests

# 5. Smoke-test the actual CLI (THIS is the spec's acceptance test)
printf 'name,note\n"Smith, John","hello, world"\n' | csv2jsonl
# expected stdout:
# {"name":"Smith, John","note":"hello, world"}

# 6. The literal invocation from the spec
csv2jsonl < tests/data/simple.csv > /tmp/out.jsonl
cat /tmp/out.jsonl
```

If `python3 --version` reports >= 3.9 and `pip install -e '.[dev]'` succeeds, **steps 3 and 5 are the verification**. Step 5 is the one that proves the spec is satisfied; everything else is hygiene.

### CI (out of scope but worth a paragraph)

If this graduates beyond a one-off: a single `.github/workflows/ci.yml` running `pip install -e '.[dev]' && pytest -q && ruff check` on Python 3.9, 3.11, 3.13, on ubuntu-latest. Maybe 20 lines total. Not building it now because the spec didn't ask.

---

## 6. Open questions I'd raise *before* writing code

If I could ask the user one round of questions, these are them — ranked by how much they could change the design:

1. **Is this called once on a 1 MB file, or millions of times in a hot loop, or once on a 50 GB file?** Changes whether we care about Python startup time (~30 ms cold) or peak RSS. Current plan handles all three but optimizes none.
2. **Should I do any type inference at all** (numbers as numbers, `""` as null, `"true"/"false"` as bools)? Default answer = no; confirming costs nothing.
3. **What should happen on a malformed row** — extra fields, unterminated quote, decode error? My plan: fail loud with row number to stderr. If you want best-effort "skip and warn" instead, that's a flag.
4. **Distribution model**: ad-hoc script in a repo? `pipx install`? Internal PyPI? Vendored single-file? Affects whether the `pyproject.toml` matters at all — for a one-off you could skip packaging entirely and ship a single 40-line `csv2jsonl.py` chmod +x.

If the answer to #4 is "single-file script, I'll just copy it onto a server", the entire `pyproject.toml` + `src/` + entry-point apparatus is dead weight, and the right deliverable is one file plus a shebang. I'd want to know that before building the package layout above.

---

## 7. Estimated size of the actual deliverable

- `cli.py`: ~40–60 lines including `--help`.
- `pyproject.toml`: ~25 lines.
- Tests: ~150 lines including fixtures.
- Total: well under 300 lines of human-written code.

If the eventual code is meaningfully larger than that, something has gone wrong with scope and I should stop and re-read this plan.
