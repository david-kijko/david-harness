SEMI-FORMAL GREENFIELD CONSTRUCTION CERTIFICATE

DEFINITIONS
D1: SUFFICIENT iff every Rn has at least one created file/test mapped to it.
D2: MINIMAL iff every created file, dependency, and concept discharges
    at least one Rn or contract. No file, dep, or layer without justification.
D3: INTERNALLY COHERENT iff the chosen interfaces, data model, runtime
    assumptions, and verification strategy do not contradict one another.
D4: VERIFIABLE iff there is a runnable command that exercises a user-visible
    path AND every Rn is covered by at least one such command.

SPEC (verbatim from the user)
"Build me a CLI tool that reads CSV from stdin and writes JSON Lines to stdout. Each row becomes one JSON object using the header row as keys. Quoted fields with embedded commas should be parsed correctly. The tool should be invokable as `csv2jsonl < input.csv > output.jsonl`. Python is fine."

SPEC DECOMPOSITION  (atomic, testable)
R1: Reads CSV from stdin (no filename argument required for the spec invocation).
    Non-goal: reading from a file path argument; reading from URLs/S3.
R2: Writes one JSON object per CSV row to stdout, using the first (header) row as keys.
    Non-goal: emitting a JSON array; pretty-printing; sorting keys.
R3: Uses RFC-4180-style CSV parsing — quoted fields with embedded commas are parsed as one field
    (e.g. `"a,b",c` → two fields `a,b` and `c`).
    Non-goal: alternate delimiters (TSV, semicolon), custom dialects via flags, type inference.
R4: Invocable on the shell as `csv2jsonl < input.csv > output.jsonl`
    (i.e. installs an executable named `csv2jsonl` on PATH).
    Non-goal: subcommands; a separate library API surface; Windows .exe packaging.
R5: Output conforms to the JSON Lines convention: one JSON value per line,
    `\n` line terminator, UTF-8 (per https://jsonlines.org/).
    Non-goal: gzip output, MIME negotiation, schema generation.

OPEN ASSUMPTIONS
A1: All CSV cells are emitted as JSON strings (no type inference). The spec says
    "Each row becomes one JSON object using the header row as keys" — it does not
    promise that the string `"3"` becomes the number `3`. Type inference is a
    surprise, and a one-line pipeline like `csv2jsonl | jq 'tonumber'` is the right
    place to do it. (Flagged as non-goal in R3.)
R2-tied A2: Empty cells are emitted as the empty string `""`, not `null`. The CSV
    standard does not distinguish "" from missing, and silently coercing is
    information-destroying.
A3: The user's environment is POSIX with Python ≥ 3.9 available (Python 3.9 is in
    security-only support, 3.10+ widely deployed; we will pin >=3.9 to be safe).
A4: Files may be large; the implementation must stream row-by-row, not load the
    whole file into memory. The user said "you don't know if it'll handle huge
    files" — streaming is the safe-by-default choice; in-memory would be a
    one-line "fix" if performance ever flips.
A5: Input is UTF-8 (matches Python's default stdin encoding on modern systems and
    matches the JSONL spec output requirement). A leading UTF-8 BOM in the first
    cell of the header would corrupt the first key — we will open stdin with the
    `utf-8-sig` codec to strip a BOM if present (verified gap; see GAP TABLE).
A6: CSV rows with MORE cells than the header has columns are an error (raise and
    exit 1) rather than silently dropping or stuffing into a `null` key. Verified
    via the GAP TABLE: stdlib's default behavior is to put extras under the
    Python literal `None` as the dict key, which would JSON-serialize as the
    string `"null"` and silently corrupt downstream consumers.
A7: CSV rows with FEWER cells than the header has columns get the missing keys
    set to the empty string `""` (passing `restval=""` to DictReader). Stdlib
    default of `None` would emit JSON `null`, conflating "missing cell" with
    "explicit null" — a downstream-confusion bug.
A8: A CSV file with zero data rows (header only) is valid input and produces zero
    output lines, exit 0.
A9: A completely empty input (zero bytes) is valid input and produces zero output
    lines, exit 0 — there is no header to require.

(If the user disagrees with any of A1–A9, they will say so on the next turn; flagging is
the point. We will not silently pick an interpretation.)

GAP IDENTIFICATION  (mandatory)

Searches run (exa):
  - "csv to jsonl python stdlib best practices command line" — surfaced csvkit's csvjson,
    pypi/csv-jsonl, jsonl.help
  - "python csv DictReader extra fields restkey behavior default" — surfaced
    docs.python.org csv module page and bpo-40013
  - "csvkit csvjson convert csv to json line stream output" — surfaced csvkit
    docs and source
  - "python BrokenPipeError sigpipe handling cli stdout pipe head" — surfaced bpo-46492
    and the canonical SIGPIPE/SIG_DFL fix
  - "csv DictReader UTF-8 BOM excel encoding handling" — surfaced the BOM-in-first-key
    StackOverflow class of bug

Deep reads (firecrawl):
  - https://docs.python.org/3/library/csv.html (canonical csv module docs)
  - https://docs.python.org/3/library/json.html (canonical json module docs)
  - https://jsonlines.org/ (the JSONL spec — UTF-8, `\n` terminator, no BOM)
  - https://github.com/wireservice/csvkit/blob/master/csvkit/utilities/csvjson.py
    (prior art: csvkit's csvjson supports `--stream` for JSONL; uses agate as a
    heavyweight intermediate and is *not* a model for a 50-line tool)

In-process verification (`python3 -c`) on this machine to confirm runtime behavior
matches the docs (Python 3.x stdlib):
  - `json.dumps({'k':'á'})` → `{"k": "\\u00e1"}`  (confirmed `ensure_ascii=True` default)
  - `csv.get_dialect('excel')` → delimiter `,`, quotechar `"`, doublequote True,
    lineterminator `'\\r\\n'`, skipinitialspace False
  - `DictReader` extras row: `{'a': '1', 'b': '2', None: ['3', '4']}`
  - `DictReader` missing row: `{'a': '1', 'b': '2', 'c': None}`

GAP TABLE:

| Initial assumption (training-time guess) | External source consulted | What the source actually says | Gap status |
|---|---|---|---|
| `csv.DictReader` drops extra cells silently | https://docs.python.org/3/library/csv.html ("If a row has more fields than fieldnames, the remaining data is put in a list and stored with the fieldname specified by *restkey*") + runtime check | Extras are put in a list under the key `restkey` (defaults to Python `None`). With default `restkey=None` the dict literally has `None` as a key; `json.dumps` will then serialize the key as the string `"null"`. | REFUTED — must explicitly choose: raise on extras (A6) OR set `restkey="_extras"`. We pick raise. |
| Missing cells in `DictReader` become `""` | https://docs.python.org/3/library/csv.html + runtime check | Default `restval=None` → missing cells become Python `None` → JSON `null`. The empty-string default is *not* the stdlib default. | REFUTED — must pass `restval=""` explicitly to match A7. |
| `json.dumps` outputs raw UTF-8 by default | https://docs.python.org/3/library/json.html (signature: `dumps(..., ensure_ascii=True, ...)`) + runtime check | Default `ensure_ascii=True` → non-ASCII chars are escaped to `\\uXXXX`. JSONL spec recommends UTF-8 (https://jsonlines.org/), which `\\uXXXX` is technically valid for but is unfriendly to humans and larger on disk. | REFINED — pass `ensure_ascii=False` so `é` stays as the byte `é`. |
| Excel dialect uses `\\n` line terminator | runtime check | `lineterminator='\\r\\n'` for the excel dialect — but lineterminator only affects writing, not reading. Reader normalizes line endings via the underlying file iterator, which is fine when stdin is opened in text mode with default `newline=` handling. The csv docs explicitly recommend `newline=''` to preserve embedded newlines inside quoted fields. | CONFIRMED-WITH-CAVEAT — must reconfigure `sys.stdin` to `newline=''` (use `io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8-sig', newline='')`). |
| A CSV header `\\ufeffname,age` (UTF-8 BOM) gives keys `["name","age"]` | runtime check + StackOverflow class | Without BOM stripping, the first key is literally `"\\ufeffname"`. With `encoding='utf-8-sig'`, Python strips the BOM. | REFUTED — must use `utf-8-sig` for stdin to handle BOM-laden Excel exports. |
| Writing to a closed pipe (e.g. `csv2jsonl < big.csv \| head`) is silently fine | https://bugs.python.org/issue46492 + bpo-33550 | Python raises `BrokenPipeError` on the next flush after the downstream closes; default behavior dumps an ugly traceback to stderr. Idiomatic fix is to set `signal(SIGPIPE, SIG_DFL)` at startup OR catch `BrokenPipeError` and exit cleanly. | REFUTED — must add explicit handling. We choose `signal(SIGPIPE, SIG_DFL)` on POSIX (no-op on Windows). |
| csvkit's `csvjson --stream` is the right reference shape | https://github.com/wireservice/csvkit/blob/master/csvkit/utilities/csvjson.py | csvjson is 298 LOC and pulls in `agate` (a heavyweight tabular library) plus the rest of csvkit's CLI scaffolding. Useful as a feature reference for `--stream` flag semantics; *not* a structural model for a one-purpose 50-line tool. | CONFIRMED + we explicitly REJECT importing csvkit/agate (see ADVERSARIAL). |
| `csv.reader` is enough; we don't need `DictReader` | docs + runtime | True technically (we could zip(header, row) by hand), but `DictReader` already implements header + restkey + restval semantics correctly, and using it is one line shorter, not longer. | CONFIRMED — use DictReader; it's the minimal stdlib primitive that maps to R2. |

(Refuted/refined ratio: 5 of 8 rows are REFUTED or REFINED — well above the 30% threshold.
The two REFUTED items about `restkey`/`restval` defaults and the BOM/SIGPIPE items are
exactly the kind of bugs that would have shipped in a from-memory implementation.)

CONSTRAINTS AND CONTEXT
C-runtime:    Python ≥ 3.9 (CPython). Stdlib only.
C-deploy:     Single-file installable script with a console-script entry point.
              Runs anywhere Python runs; no compiled deps.
C-storage:    None — purely stream-in/stream-out.
C-perf:       Streaming, O(1) memory in row count. No specific latency/throughput
              target was given (A4); streaming is the safe default.
C-security:   None — no network, no files, no auth, no eval. Reads stdin, writes stdout.
              Threat surface is malformed CSV (handled by raising).
C-user:       "Python is fine." User did not ask for a specific package layout,
              specific test framework, or specific tooling. We optimize for
              "fresh clone runs `pytest` and gets green."

DESIGN OPTIONS CONSIDERED  (guards G1, G2, G4)

| Option | Sketch | Pros | Cons | Rejected because |
|---|---|---|---|---|
| A: Single-module pure-stdlib package, console-script entry point, src/ layout, pytest, no runtime deps | `src/csv2jsonl/__init__.py` + `__main__.py` + `cli.py` (~50 LOC); pyproject.toml declares `[project.scripts] csv2jsonl = "csv2jsonl.cli:main"`; tests use stdlib `subprocess` to invoke the installed script. | Stdlib-only (R3+R5 satisfied by csv+json), one runtime concept, easy to install with `pip install -e .`, `csv2jsonl` ends up on PATH automatically per R4, tests exercise the actual user-visible path. | Slightly more files than a single-script approach (pyproject.toml, package dir). | CHOSEN — minimum surface that satisfies R4 properly (without a packaging step, `csv2jsonl < input` requires the user to manually `chmod +x` and PATH-fiddle, which fails the "fresh clone runs the tool" test). |
| B: Single shebanged script `csv2jsonl` at repo root | One file, no pyproject.toml | Smaller surface | "Fresh clone" install story is vague; user must chmod +x and PATH it manually. Also no clean test entry point — tests have to invoke the script by relative path, which is brittle on CI. | REJECTED — fails D4 (verifiable install path), and the LOC saving is illusory because we need pyproject.toml anyway for pytest discovery. |
| C: Use csvkit (`csvjson --stream`) as a thin wrapper | Subprocess shim | Reuses existing tool | Adds csvkit + agate + their transitive deps for what is fundamentally one stdlib call. G2 violation. Also bypasses the spec ("Build me a CLI") — the user asked us to build it, not to wrap an existing tool. | REJECTED — see ADVERSARIAL #2. |
| D: Use Click or Typer for argument parsing | Same shape as A but with Click | "Standard" CLI ergonomics | Spec has zero arguments. The CLI takes its input from stdin, writes to stdout, has no flags. Adding Click is G2 (unjustified dependency) and G4 (framework-of-the-week). | REJECTED — argparse with zero arguments is one line and we don't even need argparse. |
| E: Do nothing — defer | — | — | Spec is concrete; user is waiting. | REJECTED. |

Chosen option: **A** — minimal stdlib package with a console-script entry point.
  - Satisfies R1 (stdin), R2 (DictReader → dict → json.dumps line), R3 (csv module's
    excel dialect is RFC-4180-ish), R4 (`[project.scripts]` puts `csv2jsonl` on PATH),
    R5 (writes `json.dumps(...) + "\n"`).
  - Respects C-runtime (Python stdlib only), C-deploy (one `pip install` away),
    C-storage (streaming generator), C-perf (O(1) row memory),
    C-security (no I/O beyond stdin/stdout), C-user (Python).
  - Simpler than alternatives because: 0 runtime deps, 1 source file with
    real logic, 1 test file, 1 manifest.

MINIMAL ARCHITECTURE DECISION  (guards G1)

Modules / files to create:

| Module | Purpose | Discharges Rn / Cn / Initial-Contract | Why no smaller design suffices |
|---|---|---|---|
| `src/csv2jsonl/__init__.py` | Package marker; exposes `convert(in_stream, out_stream)` for in-process reuse and testing. | R1, R2, R3, R5, IC1 | Need a package because `[project.scripts]` references a Python entry point. The `convert` function is reused by both the CLI entry and the in-process tests, so it's not a single-use abstraction (G1 check passes). |
| `src/csv2jsonl/cli.py` | `main()` — wires `sys.stdin` (with `utf-8-sig`, `newline=''`), `sys.stdout`, SIGPIPE handling, exit codes. Calls `convert`. | R1, R4, IC2 (CLI contract), INV1 | Separating CLI wiring from logic keeps the logic testable without subprocess (ADVERSARIAL #3). |
| `tests/test_convert.py` | In-process unit tests for `convert()` covering R1–R3, R5, A6, A7, A8, A9. | R1, R2, R3, R5, NT1–NT6 | Fast, deterministic, no subprocess. |
| `tests/test_cli_smoke.py` | End-to-end smoke test: `subprocess.run(["csv2jsonl"], input=..., ...)` after editable install. | R4, NT-smoke, D4 | The only test that proves the spec invocation `csv2jsonl < input.csv > output.jsonl` actually works. |
| `pyproject.toml` | PEP 621 metadata, `[project.scripts] csv2jsonl = "csv2jsonl.cli:main"`, `[build-system]` with setuptools, dev-deps `[project.optional-dependencies] dev = ["pytest>=7"]`. | R4, C-runtime, D4 | Required for `pip install -e .[dev]` to work and to put `csv2jsonl` on PATH. |
| `README.md` | One-screen install + run + test instructions. | D4 | A fresh clone needs to know which two commands to run. |
| `.gitignore` | Standard Python ignores (`__pycache__`, `*.egg-info`, `.pytest_cache`, `dist/`, `build/`). | (housekeeping) | Prevents accidental commits of build artifacts. |

(Total: 7 files. No `Makefile`, no `tox.ini`, no `.pre-commit-config.yaml`,
no GitHub Actions workflow, no Dockerfile — none were asked for, none discharge an Rn.)

Dependencies to add:

| Dependency | Version | Why this exact dep | Could we do without? |
|---|---|---|---|
| (runtime: none) | — | csv + json + sys + signal + io are all stdlib. | n/a — already without. |
| pytest | >=7 | Test runner; standard in the Python world; one `pip install` away. | Yes (could use `python -m unittest`), but pytest gives readable assertion diffs and parametrize for ~7 test cases, which keeps test code under 50 lines. The sole dev dep. |

(setuptools is a build-system dep declared in `[build-system]`, not a runtime dep,
and is provided by pip during install; not listed as a "dependency to add".)

INITIAL CONTRACTS AND INVARIANTS

IC1: `csv2jsonl.convert(in_stream: TextIO, out_stream: TextIO) -> int`
     Pre: `in_stream` is a text-mode iterable yielding CSV-formatted lines (UTF-8,
          with embedded newlines inside quoted fields preserved — i.e. opened
          with `newline=''`). `out_stream` is a text-mode writable.
     Post: For each non-blank data row in input, writes exactly one line
           `json.dumps(row_dict, ensure_ascii=False) + "\n"` to `out_stream`,
           where `row_dict` maps each header column name (str) → cell value (str).
           Returns the number of rows written.
     Errors:
        - Empty input (no header): writes 0 rows, returns 0 (no error).
        - Header-only input: writes 0 rows, returns 0.
        - Row with MORE cells than header columns: raises `csv.Error`
          subclass `csv2jsonl.RowError` with row number; CLI catches and
          exits 1 to stderr.
        - Row with FEWER cells than header: missing fields filled with `""`
          (per A7); not an error.
        - Malformed quoting raises `csv.Error`; CLI catches and exits 1.

IC2: `csv2jsonl.cli.main(argv: list[str] | None = None) -> int`
     Pre: argv is None (uses sys.argv) or a list. With our spec there are no
          recognized flags; any argv beyond the program name causes exit 2
          and a one-line usage message. (argparse-free; we hand-roll because
          there are zero options.)
     Post: Returns 0 on success, 1 on data error (csv.Error), 2 on usage error,
           0 on BrokenPipeError (caller closed pipe is not a failure).
           Configures SIGPIPE to SIG_DFL on POSIX before any I/O.

INV1: stdin is read in text mode with `encoding='utf-8-sig'` and `newline=''`
      so that (a) a UTF-8 BOM is silently stripped from the first cell of the
      header, and (b) embedded `\n` inside quoted fields is preserved
      (Python csv docs explicitly require `newline=''`).
      Enforcement: `cli.main` rebinds stdin via `io.TextIOWrapper(sys.stdin.buffer, ...)`
      before calling `convert`.

INV2: Output lines are terminated with exactly one `\n` (LF), not `\r\n`,
      to match the JSONL spec.
      Enforcement: `convert` writes `json.dumps(row, ensure_ascii=False) + "\n"`
      and never uses `print` (which would respect `os.linesep` on Windows).

INV3: Memory usage is O(1) in row count — `convert` iterates the DictReader
      generator and writes each row before reading the next.
      Enforcement: `convert` uses a `for` loop, not `list(reader)`.

CREATED SURFACE

| File | Purpose | Discharges (Rn / Cn / IC / INV) |
|---|---|---|
| `src/csv2jsonl/__init__.py` | Re-exports `convert`, `RowError`. | R2, R3, R5, IC1 |
| `src/csv2jsonl/_core.py` | The `convert` function and `RowError` class — the only file with real logic. | R1, R2, R3, R5, IC1, INV2, INV3 |
| `src/csv2jsonl/cli.py` | `main()`: stdin/stdout wiring, SIGPIPE, exit codes. | R1, R4, IC2, INV1 |
| `tests/test_convert.py` | In-process unit tests. | R1, R2, R3, R5, A6, A7, A8, A9 (NT1–NT6) |
| `tests/test_cli_smoke.py` | Subprocess smoke test of the installed `csv2jsonl` entry point. | R4, NT-smoke, D4 |
| `pyproject.toml` | Build metadata, console-script registration, pytest dev extra. | R4, C-runtime, D4 |
| `README.md` | Install, run, test commands. | D4 |
| `.gitignore` | Standard Python build/test ignores. | housekeeping |

(Every row above cites at least one Rn / Cn / IC / INV — D2 check passes.)

REQUIREMENT → CODE MAPPING

R1 (read CSV from stdin) → `src/csv2jsonl/cli.py` (stdin rebinding) calling
   `convert` in `src/csv2jsonl/_core.py`. Demonstrated by `tests/test_cli_smoke.py::test_pipe_invocation`.
   Inference type: spec-decomposition (the spec literally says "reads CSV from stdin").
R2 (one JSON object per row, header as keys) → `src/csv2jsonl/_core.py::convert`
   uses `csv.DictReader` and `json.dumps`. Demonstrated by
   `tests/test_convert.py::test_basic_two_rows`.
   Inference type: pattern-reuse (DictReader gives header→dict mapping for free).
R3 (quoted fields with embedded commas parsed correctly) → `csv.DictReader`'s
   default `excel` dialect (delimiter=`,`, quotechar=`"`, doublequote=True).
   Demonstrated by `tests/test_convert.py::test_quoted_field_with_comma`
   and `tests/test_convert.py::test_doublequote_escape`.
   Inference type: invariant-preservation (Python csv module is RFC-4180-ish).
R4 (invocable as `csv2jsonl < input.csv > output.jsonl`) → `pyproject.toml`'s
   `[project.scripts] csv2jsonl = "csv2jsonl.cli:main"`. Demonstrated by
   `tests/test_cli_smoke.py::test_pipe_invocation` which actually runs
   `subprocess.run(["csv2jsonl"], stdin=PIPE, stdout=PIPE)`.
   Inference type: spec-decomposition.
R5 (JSON Lines convention: UTF-8, `\n`-terminated, one value per line) →
   `_core.py` writes `json.dumps(row, ensure_ascii=False) + "\n"`.
   Demonstrated by `tests/test_convert.py::test_jsonl_format` (asserts `\n`
   terminator and per-line valid-JSON parse).
   Inference type: invariant-preservation against jsonlines.org spec.

VERIFICATION SCAFFOLD

Test framework choice: **pytest >= 7** — chosen because it's the de-facto standard
for Python ≥ 3.9, gives readable assertion diffs, and supports `parametrize` so
the 6 test cases collapse to < 40 LOC.

Smoke command (one command, real user-visible path):
```
printf 'name,city\nAda,"Lon,don"\nGrace,NYC\n' | csv2jsonl
```
Expected output:
```
{"name": "Ada", "city": "Lon,don"}
{"name": "Grace", "city": "NYC"}
```

Build / type / lint commands:
  - Install (build): `pip install -e .[dev]`
  - Tests:           `pytest -q`
  - (No type-checker, no linter — neither was asked for; both are speculative work.)

Fixture strategy: tests pass CSV strings via `io.StringIO` directly to
`convert()` (unit tests) and via `subprocess.run(..., input=csv_str, text=True)`
(smoke test). No on-disk fixtures, no tmpdir gymnastics.

Run instructions (READMEable, exact commands a fresh clone would type):
```
git clone <repo>
cd <repo>
python3 -m venv .venv && source .venv/bin/activate     # POSIX
pip install -e '.[dev]'
pytest -q                                              # all 7 tests green
echo 'a,b
1,"2,3"' | csv2jsonl                                   # smoke
```

NEW TEST OBLIGATIONS

NT1 (R1, R2): `test_basic_two_rows` — input `"name,age\nAda,36\nGrace,85\n"`
   → output two lines, `{"name":"Ada","age":"36"}` and `{"name":"Grace","age":"85"}`.
   Runnable: `pytest -q tests/test_convert.py::test_basic_two_rows`
NT2 (R3): `test_quoted_field_with_comma` — input `'name,city\nAda,"Lon,don"\n'`
   → `{"name":"Ada","city":"Lon,don"}`.
   Runnable: `pytest -q tests/test_convert.py::test_quoted_field_with_comma`
NT3 (R3): `test_doublequote_escape` — input `'q\n"she said ""hi"""\n'`
   → `{"q":"she said \\"hi\\""}`.
   Runnable: `pytest -q tests/test_convert.py::test_doublequote_escape`
NT4 (R5, A5): `test_unicode_passthrough` — input contains `é`; assert output
   line bytes contain literal `é` (UTF-8) and not `\\u00e9` (because we set
   `ensure_ascii=False`).
   Runnable: `pytest -q tests/test_convert.py::test_unicode_passthrough`
NT5 (A8, A9): `test_empty_and_header_only` — empty input → 0 lines, exit 0;
   header-only → 0 lines, exit 0.
   Runnable: `pytest -q tests/test_convert.py::test_empty_and_header_only`
NT6 (A6, A7): `test_row_length_mismatch` — too many cells raises `RowError`;
   too few cells fills missing keys with `""`.
   Runnable: `pytest -q tests/test_convert.py::test_row_length_mismatch`
NT-smoke (R4): `test_pipe_invocation` — uses `subprocess.run(["csv2jsonl"], ...)`
   to verify the installed entry point exists on PATH and round-trips a
   3-row CSV.
   Runnable: `pytest -q tests/test_cli_smoke.py::test_pipe_invocation`
   (Requires `pip install -e .[dev]` in the active venv. README says so.)

(Every Rn has at least one NTn; one NT-smoke exists — D1, D4 satisfied.)

COUNTEREXAMPLE / SUFFICIENCY CHECK

For each Rn:
  R1: Soundness — `convert(sys.stdin, sys.stdout)` is called from `cli.main`;
      stdin is text-mode UTF-8 (with utf-8-sig and newline=''). For ANY CSV byte
      stream piped into stdin, the DictReader iterator yields rows. ✓
  R2: Soundness — DictReader uses the first row as fieldnames; for each
      subsequent row it returns a `dict[str,str]`; we serialize that dict.
      Counterexample candidate: a header row with a duplicate column name
      (e.g. `a,b,a`) — DictReader keeps the LAST occurrence in the dict
      (verified: `dict(zip(['a','b','a'],['1','2','3'])) == {'a':'3','b':'2'}`).
      This is undefined behavior in CSV (no two columns should share a name);
      we accept stdlib's behavior and document it (or could detect & raise —
      flagged but out of scope of the spec, leave as documented gotcha).
  R3: Soundness — Python's csv module is the canonical implementation of
      Excel-style CSV including RFC-4180 quote handling. Tests NT2 and NT3
      directly exhibit the embedded-comma and doubled-quote cases.
  R4: Soundness — `[project.scripts]` is the standard PEP 621 mechanism
      and pip installs it as `~/.local/bin/csv2jsonl` (or venv equivalent).
      NT-smoke literally invokes `csv2jsonl` as a subprocess, so the
      verification IS the proof.
  R5: Soundness — write `json.dumps(...) + "\n"` per row. JSONL spec requires
      `\n` (or `\r\n`) and UTF-8; we satisfy both. NT4 asserts UTF-8
      passthrough.

For each design decision:
  - One source file with logic (`_core.py`)? Could we satisfy R1–R5 with less?
    No — fewer files would mean inlining `cli.py` into `_core.py`, which
    couples wiring to logic and breaks the testability of `convert()` (G5).
  - Pytest? Could we satisfy NT1–NT-smoke with `unittest`? Yes, slightly more
    boilerplate. Pytest is one dev dep with an outsize ergonomics win on the
    parametrize axis. Keep.
  - SIGPIPE handler? Could we drop it? No — without it, `csv2jsonl < big.csv | head`
    prints a Python traceback to stderr, which is user-visible breakage.
  - utf-8-sig? Could we drop it? No — Excel's "Save as CSV UTF-8" emits a BOM,
    and without `utf-8-sig` the first dict key becomes `"\\ufeffname"`, silently
    corrupting downstream consumers.

ADVERSARIAL CHECK
1. Premature abstraction: Is any module/class/interface used in only one place?
   - `RowError` is referenced from `_core.py` (raises) and `cli.py` (catches) —
     two places, justified.
   - `convert` is called from `cli.main` and from every unit test — multi-use,
     justified.
   - No factories, no abstract base classes, no protocols. Verdict: clean.

2. Unjustified dependency: Would removing dep X mean writing > 50 lines?
   - Runtime deps: zero. Cannot remove what isn't there.
   - Pytest (dev only): replacing with `unittest` would add ~30 LOC of
     boilerplate (no parametrize). Borderline; pytest stays because the user
     gets one familiar `pytest -q` command, not a homegrown runner.

3. Untestable boundary: Can NT1 be run with NO network, NO real DB, NO LLM?
   - NT1–NT6 use `io.StringIO` — pure in-process. ✓
   - NT-smoke uses `subprocess.run(["csv2jsonl"], input=..., text=True)` — local
     process only, no network. ✓
   - There is no DB. There is no LLM. There is no network call anywhere in the
     production code. ✓

FORMAL CONCLUSION
By D1 (SUFFICIENT):           YES — every R1–R5 maps to ≥1 created file and ≥1 NT.
By D2 (MINIMAL):              YES — every file/dep cites a specific Rn/Cn/IC/INV.
By D3 (INTERNALLY COHERENT):  YES — text-mode stdin (utf-8-sig, newline='')
                              composes correctly with csv.DictReader (which
                              REQUIRES newline='' per docs); ensure_ascii=False
                              composes with the JSONL UTF-8 requirement;
                              SIGPIPE/SIG_DFL composes with stdout pipes.
By D4 (VERIFIABLE):           YES — `pip install -e '.[dev]' && pytest -q`
                              runs all 7 tests including the subprocess
                              smoke test that exercises `csv2jsonl` on PATH.

Plan is READY TO IMPLEMENT: **YES.**

---

## Appendix: implementation sketch (for the implementer; not part of the certificate)

`src/csv2jsonl/_core.py` (~25 LOC):
```python
import csv
import json

class RowError(csv.Error):
    """Raised when a CSV row has more fields than the header."""

_EXTRAS_SENTINEL = object()

def convert(in_stream, out_stream) -> int:
    reader = csv.DictReader(in_stream, restkey=_EXTRAS_SENTINEL, restval="")
    n = 0
    for i, row in enumerate(reader, start=2):  # row 1 was the header
        if _EXTRAS_SENTINEL in row:
            extras = row[_EXTRAS_SENTINEL]
            raise RowError(f"row {i}: {len(extras)} extra cell(s) beyond header")
        out_stream.write(json.dumps(row, ensure_ascii=False))
        out_stream.write("\n")
        n += 1
    return n
```

`src/csv2jsonl/cli.py` (~25 LOC):
```python
import io
import signal
import sys
from . import _core

def main(argv=None):
    argv = sys.argv if argv is None else argv
    if len(argv) > 1:
        sys.stderr.write("usage: csv2jsonl < input.csv > output.jsonl\n")
        return 2
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8-sig", newline="")
    try:
        _core.convert(stdin, sys.stdout)
    except _core.RowError as e:
        sys.stderr.write(f"csv2jsonl: {e}\n")
        return 1
    except BrokenPipeError:
        return 0
    except Exception as e:  # csv.Error, UnicodeDecodeError, etc.
        sys.stderr.write(f"csv2jsonl: {type(e).__name__}: {e}\n")
        return 1
    return 0
```

`pyproject.toml` (~15 LOC):
```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "csv2jsonl"
version = "0.1.0"
description = "Stream CSV from stdin, emit JSON Lines to stdout."
requires-python = ">=3.9"

[project.scripts]
csv2jsonl = "csv2jsonl.cli:main"

[project.optional-dependencies]
dev = ["pytest>=7"]

[tool.setuptools.packages.find]
where = ["src"]
```

(Test files and README follow the patterns specified in NT1–NT-smoke and the
"Run instructions" block above.)
