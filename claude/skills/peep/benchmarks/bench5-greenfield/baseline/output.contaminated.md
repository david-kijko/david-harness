# SEMI-FORMAL GREENFIELD CONSTRUCTION CERTIFICATE

## DEFINITIONS
- **D1 SUFFICIENT** iff every Rn has at least one created file/test mapped to it.
- **D2 MINIMAL** iff every created file, dependency, and concept discharges at least one Rn or contract.
- **D3 INTERNALLY COHERENT** iff the chosen interfaces, data model, runtime assumptions, and verification strategy do not contradict one another.
- **D4 VERIFIABLE** iff there is a runnable command that exercises a user-visible path AND every Rn is covered by at least one such command.

## SPEC (verbatim from the user)
> Build me a CLI tool that reads CSV from stdin and writes JSON Lines to stdout. Each row becomes one JSON object using the header row as keys. Quoted fields with embedded commas should be parsed correctly. The tool should be invokable as `csv2jsonl < input.csv > output.jsonl`. Python is fine.

## SPEC DECOMPOSITION (atomic, testable)
- **R1**: Read CSV from `stdin`. — *Non-goal*: reading from file paths passed as args.
- **R2**: Write JSON Lines (one JSON object per line, `\n`-terminated, no enclosing array) to `stdout`. — *Non-goal*: pretty-printed JSON, JSON arrays, NDJSON variants like `\r\n`.
- **R3**: First row is the header; subsequent rows become objects keyed by the header. — *Non-goal*: header-less mode, custom column names, type inference (everything stays a string — JSON Lines convention for csv→jsonl is preserve-as-string unless asked).
- **R4**: Quoted fields with embedded commas are parsed correctly (RFC 4180 quoting). — *Non-goal*: custom delimiters, custom quote chars, escape-char dialects beyond RFC 4180.
- **R5**: Invokable as `csv2jsonl < input.csv > output.jsonl` (i.e. an executable named `csv2jsonl` is on `PATH` after install). — *Non-goal*: GUI, daemon, library API surface.

## OPEN ASSUMPTIONS
- **A1**: All cell values stay as JSON strings. CSV has no native types; the spec did not ask for `"42" → 42` coercion. Doing it silently would be over-refinement (G6) and lossy ("007" → 7).
- **A2**: Encoding is UTF-8 for both input and output. Standard for modern pipelines; the spec does not specify, and Python 3's default `sys.stdin` text mode honors `PYTHONIOENCODING` / locale, which is correct behavior to inherit.
- **A3**: Streaming is acceptable but not required. The spec is silent on file size. We will stream row-by-row anyway because it costs nothing and avoids OOM on large inputs (one-line change vs. `list()`).
- **A4**: Rows with more/fewer fields than the header: extra fields are dropped, missing fields become empty strings — matches `csv.DictReader` defaults. Will document, not silently invent behavior.
- **A5**: Empty input (no header) produces zero output lines and exits 0. Standard Unix-pipeline behavior.
- **A6**: User has Python ≥ 3.8 available (covers every supported distro as of 2026-05).
- **A7**: "CLI tool that is invokable as `csv2jsonl`" implies the user wants a real command on `PATH`, not `python script.py`. We will provide an installable package with a console-script entry point AND a chmod+x shebang script for the no-install path.

## CONSTRAINTS AND CONTEXT
- **C-runtime**: Python ≥ 3.8 (stdlib only).
- **C-deploy**: Single-file script + standard `pyproject.toml` for `pip install .`. Runs anywhere Python runs — laptop, container, CI.
- **C-storage**: None — stateless stdin → stdout filter.
- **C-perf**: No stated requirement. Streaming row-by-row gives O(1) memory; sufficient for any plausible scale.
- **C-security**: None — no network, no file paths from input, no shell-out, no eval.
- **C-user**: "Python is fine" — language pinned to Python by the user. No other constraints.

## DESIGN OPTIONS CONSIDERED (guards G1, G2, G4)

| Option | Sketch | Pros | Cons | Verdict |
|---|---|---|---|---|
| **A**: Single `csv2jsonl.py` script using stdlib `csv.DictReader` + `json.dumps`, ~15 LOC, packaged via `pyproject.toml` console-script. | One module, one function, zero deps. | Minimal, stdlib-only, trivially auditable, fast. | None for this spec. | **CHOSEN** |
| B: Same logic but using `pandas.read_csv` + `df.to_json(orient='records', lines=True)`. | One-liner conceptually. | Familiar to data folks. | ~50 MB dep, multi-second import time, type-coerces strings into ints/floats silently (violates A1 unless `dtype=str`), overkill. | Rejected: G2/G4. |
| C: Use `click` or `typer` for arg parsing. | Pretty `--help`. | Future-proof for flags. | Spec has zero flags. Adds a dep for nothing. | Rejected: G2, G6. |
| D: Roll a custom CSV parser to "avoid" stdlib dependency. | Educational. | None vs. stdlib. | Re-implements RFC 4180; bug surface; spec explicitly mentions quoted-comma which is exactly what stdlib `csv` already handles. | Rejected: G4 inverted (NIH). |
| E: Do nothing — defer. | — | — | User asked for a tool; deferral is non-responsive. | Rejected. |

**Chosen: Option A.** Justification grounded in Rn / Cn:
- Satisfies **R1, R2, R3, R4** because `csv.DictReader` reads stdin, returns dicts keyed by header row, and parses RFC 4180 quoting (verified empirically: `python3 -c "import csv; ..."` correctly parsed `1,"2,3",4` → `{"a":"1","b":"2,3","c":"4"}`).
- Satisfies **R5** via `pyproject.toml` `[project.scripts]` entry point producing a `csv2jsonl` executable on `PATH` after `pip install .`.
- Respects **C-runtime, C-deploy, C-user** (stdlib only, runs anywhere Python runs, Python).
- Simpler than alternatives: zero third-party deps, ~15 LOC implementation.

## MINIMAL ARCHITECTURE DECISION (guards G1)

### Modules / files to create

| File | Purpose | Discharges Rn / Cn / Initial-Contract | Why no smaller design suffices |
|---|---|---|---|
| `src/csv2jsonl/__init__.py` | Package marker, exposes `main` for the entry point. | R5, IC1 | Required by `pyproject.toml` console-script entry-point form `csv2jsonl:main`. |
| `src/csv2jsonl/__main__.py` | Allows `python -m csv2jsonl` as a fallback invocation. | R5 (alt path) | One line (`from . import main; main()`); enables use without install. |
| `src/csv2jsonl/cli.py` | The actual logic: `main()` reads stdin via `csv.DictReader`, writes `json.dumps(row) + "\n"` per row to stdout. | R1, R2, R3, R4, IC1, INV1 | Cannot be smaller — this IS the program. |
| `pyproject.toml` | Project metadata, build backend (`setuptools` or `hatchling`), `[project.scripts]` entry point. | R5, C-runtime, D4 | Required for `pip install .` to produce the `csv2jsonl` executable. |
| `tests/test_cli.py` | Pytest suite exercising R1–R4 and edge cases. | NT1–NT5 | Required by D4. |
| `tests/fixtures/simple.csv` | Header + two plain rows. | NT1 | Real fixture, not inline string — exercises true stdin path. |
| `tests/fixtures/quoted.csv` | Header + row with quoted comma + row with quoted newline. | NT4 | Demonstrates R4 explicitly. |
| `tests/fixtures/empty.csv` | Zero bytes. | NT-edge-empty | Demonstrates A5 behavior. |
| `tests/fixtures/header_only.csv` | One header row, no data. | NT-edge-header-only | Demonstrates A5 behavior. |
| `README.md` | Install + run + test instructions, exact `pip install .` and `pytest` commands. | D4 | Required so a fresh clone knows what to type. |
| `.gitignore` | Standard Python ignores (`__pycache__`, `*.egg-info`, `.pytest_cache`, `dist/`, `build/`). | hygiene | One-time cost; prevents committing build artifacts. |

**Files explicitly NOT created** (each would be G1/G6):
- No `setup.py` (`pyproject.toml` is sufficient with PEP 621).
- No `Makefile` (one `pytest` command does not warrant a build tool).
- No `Dockerfile` (spec did not mention containers; Python is portable).
- No `requirements.txt` (no runtime deps; dev deps live in `pyproject.toml [project.optional-dependencies]`).
- No `tox.ini` / `nox` (one Python version, one test command).
- No CI workflow file (spec did not request CI; can be added if asked).
- No `LICENSE` (not requested; would invent a policy decision the user has not made — flag instead in README that license is TBD).
- No `src/csv2jsonl/parser.py` / `src/csv2jsonl/writer.py` split (G1 — premature module split for ~15 LOC).
- No logging, no `--verbose`, no `--help` beyond what argparse-free script gives (spec has no flags).

### Dependencies to add

| Dependency | Version | Why this exact dep | Could we do without? |
|---|---|---|---|
| `pytest` | `>=7,<9` (dev only) | Standard Python test runner; required for NT1–NT5 to be runnable as `pytest`. | Yes — could use `unittest` from stdlib; chosen `pytest` because fixtures + parametrize collapse the test file by ~40%. Acceptable: dev-only, not a runtime dep. |
| `setuptools` or `hatchling` | latest (build only) | PEP 517 build backend, declared in `pyproject.toml [build-system]`. | No — required by `pip` to build the wheel that creates the `csv2jsonl` script. Will use `setuptools` (ships with `pip`, zero install cost). |

**Runtime dependencies: zero.** Everything the program does at runtime is stdlib (`csv`, `json`, `sys`).

## INITIAL CONTRACTS AND INVARIANTS

- **IC1**: `csv2jsonl.cli.main() -> int`
  - **Pre**: `sys.stdin` is a readable text stream containing zero or more bytes; `sys.stdout` is writable.
  - **Post**: For each data row in the input CSV, exactly one line of valid JSON (object form) has been written to stdout, in input order, terminated by `\n`. The keys of each object equal the header row's field names (in order, but JSON object key order is insertion-preserving in Python ≥ 3.7).
  - **Errors**: Returns non-zero and writes a one-line message to stderr if (a) `csv.Error` is raised, or (b) `BrokenPipeError` from a downstream consumer closing the pipe early (handle gracefully — exit 0, suppress traceback; this is standard Unix-filter etiquette). Returns 0 on success and on empty input.

- **INV1**: The tool is purely streaming — at most one row is held in memory at a time. Enforcement: never call `list(reader)`; iterate `for row in reader`. Will be checked by code review on `cli.py` and implicitly by NT-large.

- **INV2**: All values in emitted JSON objects are strings. Enforcement: rely on `csv.DictReader`'s default behavior (no type coercion); never call `int()` / `float()` on cell values.

- **INV3**: Output is line-delimited JSON with `\n` separators only (not `\r\n`), one object per line, no trailing comma, no enclosing array. Enforcement: write `json.dumps(row, ensure_ascii=False) + "\n"` per row; never use `json.dumps(list_of_rows)`.

## CREATED SURFACE — full file list

(Same as the table above. Restated as a flat checklist for the implementer.)

1. `pyproject.toml`
2. `README.md`
3. `.gitignore`
4. `src/csv2jsonl/__init__.py`
5. `src/csv2jsonl/__main__.py`
6. `src/csv2jsonl/cli.py`
7. `tests/test_cli.py`
8. `tests/fixtures/simple.csv`
9. `tests/fixtures/quoted.csv`
10. `tests/fixtures/empty.csv`
11. `tests/fixtures/header_only.csv`

Total: **11 files**, **0 runtime deps**, **1 dev dep** (`pytest`).

## REQUIREMENT → CODE MAPPING

| Req | Satisfied by | Demonstrated by |
|---|---|---|
| R1 (read CSV from stdin) | `cli.py` `csv.DictReader(sys.stdin)` | NT1, NT-smoke |
| R2 (write JSONL to stdout) | `cli.py` `sys.stdout.write(json.dumps(row) + "\n")` | NT1, NT-smoke |
| R3 (header-row keys) | `csv.DictReader` default behavior | NT1, NT2 |
| R4 (quoted commas parsed) | `csv.DictReader` (RFC 4180 default dialect) | NT4 |
| R5 (`csv2jsonl` on PATH) | `pyproject.toml [project.scripts] csv2jsonl = "csv2jsonl.cli:main"` | NT-smoke (invokes the installed binary, not `python -m`) |

Inference type for each: **spec-decomposition** (R1–R4 map to direct stdlib calls); **pattern-reuse** (R5 maps to PEP 621 console-scripts pattern). See `references/claim-types.md`.

## VERIFICATION SCAFFOLD (guards G3, G5)

- **Test framework**: `pytest >=7,<9`. Chosen because `parametrize` + `capsys` + `monkeypatch` collapse stdin/stdout testing to ~3 lines per case, vs. ~10 with `unittest`. Dev-only dep.
- **Smoke command** (real user-visible path, post-install):
  ```sh
  printf 'name,note\nAlice,"hi, there"\nBob,plain\n' | csv2jsonl
  ```
  Expected stdout (exact):
  ```
  {"name": "Alice", "note": "hi, there"}
  {"name": "Bob", "note": "plain"}
  ```
- **Build / lint / type commands**: none mandated (spec has no quality bar; adding `ruff`/`mypy` would be G6). README notes "ruff/mypy optional" without including them in `pyproject.toml`.
- **Fixture strategy**: real CSV files under `tests/fixtures/`, opened by tests and piped through `main()` via `monkeypatch.setattr(sys, "stdin", open(fixture))` + `capsys.readouterr()`. No mocks, no network, no DB — fully hermetic.
- **Run instructions** (READMEable, exact commands a fresh clone types):
  ```sh
  git clone <repo> && cd csv2jsonl
  python3 -m venv .venv && source .venv/bin/activate
  pip install -e '.[dev]'
  pytest                                                          # runs NT1–NT5
  printf 'a,b\n1,"2,3"\n' | csv2jsonl                              # smoke
  ```

## NEW TEST OBLIGATIONS

| ID | Test | Demonstrates | Runnable |
|---|---|---|---|
| **NT1** | `test_basic_two_rows` — feed `simple.csv`, assert two JSON-object lines with correct keys/values. | R1, R2, R3 | `pytest tests/test_cli.py::test_basic_two_rows` |
| **NT2** | `test_header_keys_preserved` — assert object keys equal header row in order. | R3 | `pytest -k header_keys_preserved` |
| **NT3** | `test_unicode_passthrough` — feed UTF-8 with non-ASCII (e.g. `名前,メモ\n太郎,こんにちは\n`); assert exact passthrough with `ensure_ascii=False`. | A2 | `pytest -k unicode_passthrough` |
| **NT4** | `test_quoted_comma_and_newline` — feed `quoted.csv` containing `"hello, world"` and a `"line1\nline2"` field; assert correct JSON values. | **R4** (the spec's explicit case) | `pytest -k quoted_comma_and_newline` |
| **NT5** | `test_empty_input_exits_zero` and `test_header_only_no_rows` — feed `empty.csv` and `header_only.csv`; assert zero stdout lines and exit 0. | A5 | `pytest -k empty_input_exits_zero or header_only_no_rows` |
| **NT-smoke** | `test_installed_binary_smoke` — `subprocess.run(["csv2jsonl"], input=..., capture_output=True)`; asserts the entry-point installed by `pip install -e .` is on PATH and produces correct output. | **R5** (the only test that proves R5; unit tests of `main()` do not) | `pytest -k installed_binary_smoke` |

Every Rn has ≥ 1 NT. NT-smoke exists.

## COUNTEREXAMPLE / SUFFICIENCY CHECK

For each Rn, soundness sketch:

- **R1**: `csv.DictReader(sys.stdin)` consumes whatever is on stdin. ∀ readable text stream → reader iterates rows. **Sound.** No counterexample in scope.
- **R2**: `sys.stdout.write(json.dumps(d) + "\n")` for each `d` produces exactly N lines for N input rows. `json.dumps` of a `dict[str,str]` is total. **Sound.** Edge: `BrokenPipeError` if downstream closes early — handled by IC1's error clause (catch and exit 0 to be a polite Unix filter).
- **R3**: `csv.DictReader`'s contract is that the first row becomes `fieldnames` and subsequent rows are zipped into `dict(zip(fieldnames, row))`. Verified empirically. **Sound.**
- **R4**: `csv.DictReader` uses the `excel` dialect by default, which implements RFC 4180 double-quote escaping. Verified empirically: `1,"2,3",4` → `{"a":"1","b":"2,3","c":"4"}`. **Sound.**
- **R5**: PEP 621 `[project.scripts]` produces a stub script in the venv's `bin/` calling `csv2jsonl.cli:main`. NT-smoke verifies this exists and works post-install. **Sound** modulo `pip install` succeeding.

For each design decision, "could we satisfy with less?":
- One module instead of two (parser + writer split): **already the case** — single `cli.py`. ✓
- Drop `pytest` dev dep, use `unittest`: **could**, but ~40% more LOC for tests with no benefit; pytest is a near-universal Python convention; cost is dev-only. Acceptable.
- Drop `pyproject.toml`, ship just `csv2jsonl.py` with `chmod +x` and a shebang: **could**, but R5 ("invokable as `csv2jsonl`") is most idiomatically and portably solved by a real installed entry point. The shebang-only path requires the user to manually copy to a PATH dir or alias. Will mention in README as alternative but make `pip install` the primary path.

## ADVERSARIAL CHECK

1. **Premature abstraction (G1)?** No classes, no factories, no `Reader`/`Writer` split. The whole program is one `main()` function in one file. ✓
2. **Unjustified dependency (G2)?** Zero runtime deps. One dev dep (`pytest`) saves >50 LOC of test boilerplate vs. `unittest`. Justified. ✓
3. **Untestable boundary (G5)?** All tests run with no network, no DB, no LLM. Stdin is monkeypatched to open file fixtures; stdout is captured via `capsys`. NT-smoke uses `subprocess` against the locally-installed entry point — fully hermetic to the dev machine. ✓

## FORMAL CONCLUSION

- By **D1 (SUFFICIENT)**: **YES** — every R1–R5 has ≥ 1 file and ≥ 1 NT.
- By **D2 (MINIMAL)**: **YES** — every file in CREATED SURFACE cites a Rn / IC / INV; zero runtime deps; one dev dep with explicit justification; no speculative abstractions.
- By **D3 (INTERNALLY COHERENT)**: **YES** — stdlib csv handles R4; stdlib json handles R2; PEP 621 entry-point handles R5; pytest fixtures handle V; nothing contradicts.
- By **D4 (VERIFIABLE)**: **YES** — `pytest` runs NT1–NT5 + NT-smoke from a fresh clone after `pip install -e '.[dev]'`; smoke command is one shell line.

**Plan is READY TO IMPLEMENT: YES.**

---

## Appendix A: exact commands a fresh clone would type

```sh
# 1. Clone and enter
git clone <repo-url> csv2jsonl
cd csv2jsonl

# 2. Isolated environment (recommended, not required)
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Install (editable + dev extras pulls in pytest)
pip install -e '.[dev]'

# 4. Run tests (must be green)
pytest -q

# 5. Smoke-test the installed binary
printf 'name,note\nAlice,"hi, there"\nBob,plain\n' | csv2jsonl
# Expected:
# {"name": "Alice", "note": "hi, there"}
# {"name": "Bob", "note": "plain"}

# 6. Real-world invocation (the spec's stated form)
csv2jsonl < input.csv > output.jsonl
```

## Appendix B: implementation sketch for `src/csv2jsonl/cli.py` (for the implementer)

Approximate target — ~15 lines, stdlib only:

```python
import csv, json, sys

def main() -> int:
    try:
        reader = csv.DictReader(sys.stdin)
        for row in reader:
            sys.stdout.write(json.dumps(row, ensure_ascii=False) + "\n")
        return 0
    except BrokenPipeError:
        # Downstream closed the pipe (e.g. `csv2jsonl < big.csv | head`)
        try: sys.stdout.close()
        except Exception: pass
        return 0
    except csv.Error as e:
        print(f"csv2jsonl: parse error: {e}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    sys.exit(main())
```

## Appendix C: explicitly considered and rejected scope creep

| Tempting feature | Why rejected |
|---|---|
| `--delimiter` / `--quotechar` flags | Not in spec; would need argparse and another ~10 LOC of test surface. Add only if asked. |
| Type inference (`"42"` → `42`) | Lossy (`"007"` → `7`); not in spec; A1 explicitly preserves strings. |
| `--ndjson` vs `--jsonl` switch | Same format. Spec said JSON Lines. Done. |
| Reading from file path argv | Spec explicitly says "from stdin". Shell redirection covers it. YAGNI. |
| Streaming gzip support | Not in spec. `zcat input.csv.gz \| csv2jsonl` already works. |
| Progress bar | Not in spec; would add `tqdm` dep for nothing. |
| Logging framework | Not in spec; print to stderr on error is sufficient. |
| Schema validation against a JSON Schema | Not in spec; would add `jsonschema` dep. |
| Async / multiprocessing | Not in spec; one Python process saturates a single pipe just fine for any plausible input. |
