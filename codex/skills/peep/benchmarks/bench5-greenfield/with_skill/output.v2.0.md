```
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
"Build me a CLI tool that reads CSV from stdin and writes JSON Lines to stdout.
Each row becomes one JSON object using the header row as keys. Quoted fields
with embedded commas should be parsed correctly. The tool should be invokable
as `csv2jsonl < input.csv > output.jsonl`. Python is fine."

SPEC DECOMPOSITION  (atomic, testable)
R1: Reads CSV bytes from stdin (no filename arg required for the canonical invocation).
    — Non-goal: reading from arbitrary file paths, URLs, multiple inputs.
R2: First non-empty row is treated as the header; its cells become JSON keys for
    every subsequent row.
    — Non-goal: header-less input, schema inference, type coercion, renaming keys.
R3: Each subsequent CSV row is emitted as exactly one JSON object on its own line
    (JSON Lines / NDJSON: one compact JSON value + `\n` per row, no surrounding
    array, no trailing comma).
    — Non-goal: pretty-printing, JSON arrays, JSON Schema output.
R4: Quoted fields containing commas (and the standard RFC-4180 corollaries:
    embedded newlines inside quotes, doubled quotes `""` as escape) are parsed
    correctly so that `"a,b",c` -> two cells `a,b` and `c`.
    — Non-goal: custom delimiters/quote chars, BOM stripping config, dialect sniffing.
R5: Tool is invokable as `csv2jsonl < input.csv > output.jsonl` from a shell after
    install — i.e. it is on PATH and reads stdin / writes stdout (no prompts, no
    interactive TTY behaviour).
    — Non-goal: GUI, REPL, daemon mode, --help flag is a stretch goal not required.
R6: Python implementation acceptable ("Python is fine").
    — Non-goal: choosing a faster language; vendoring a parser.

OPEN ASSUMPTIONS
A1: Input encoding is UTF-8. The spec says nothing; UTF-8 is the modern default
    and matches Python 3's text-stdin default on most systems. We will not add
    a --encoding flag (would be invented requirement, G6).
A2: "JSON object" means a flat object {key: string_value, ...}. All values stay
    as strings; no numeric / boolean / null coercion. The CSV format itself has
    no types, so coercion would require a guess, which the spec does not ask for.
A3: When a data row has more cells than the header, extra cells are dropped;
    when fewer, missing keys map to empty string "". This matches Python's
    csv.DictReader default and is the least-surprising behaviour. Documented
    in README.
A4: Empty input (zero rows) -> zero output lines, exit 0. Header-only input
    (one row) -> zero output lines, exit 0.
A5: This is a one-off question with no follow-up, so we optimise for "works on
    a laptop today, easy to read in 6 months", not for "10 GB files at line
    rate". We will still stream row-by-row (not slurp the file) so behaviour
    on a large file degrades gracefully, but we will not add chunked I/O,
    multiprocessing, or memory-mapped reads.
A6: No requirement was given for exit codes on malformed CSV. We will let the
    stdlib `csv` module's exceptions propagate as a non-zero exit with a
    stderr traceback — acceptable for a one-off CLI; documented.

CONSTRAINTS AND CONTEXT
C-runtime:    Python 3.9+ (widely available; nothing newer needed; csv + json
              are stdlib in every supported version).
C-deploy:     Single Python package installable via `pip install .` exposing a
              `csv2jsonl` console-script entry point. No container, no service.
C-storage:    None — pure stdin->stdout filter, stateless.
C-perf:       No requirement (A5). Target: streaming, O(1) memory per row,
              O(1) memory beyond header dict. Acceptable throughput is whatever
              the stdlib `csv` module gives.
C-security:   None. No network, no filesystem writes (caller's shell handles
              the redirect), no auth, no secrets. Threat model: a malicious CSV
              cannot do worse than crash the process or produce garbage JSON
              (no eval, no shell-out).
C-user:       "Python is fine" — explicit user permission for Python, so we
              don't need to defend the language choice. User pressed Enter
              and is waiting => prefer the smallest credible answer.

DESIGN OPTIONS CONSIDERED  (guards G1, G2, G4)
| Option | Sketch | Pros | Cons | Rejected because |
|---|---|---|---|---|
| Opt A: stdlib only, single module, console-script entry point | `csv.DictReader(sys.stdin)` -> `json.dumps(row)` -> `print`. One file `csv2jsonl.py`, `pyproject.toml` exposes `csv2jsonl = "csv2jsonl:main"`. Tests use pytest. | Zero runtime deps. Stdlib `csv` is RFC-4180-ish and handles quoted commas + embedded newlines + `""` escape — exactly R4. Trivial to read. Trivial to install. | pytest is a dev dep (not runtime). | CHOSEN |
| Opt B: pandas / polars `read_csv` -> `to_json(orient="records", lines=True)` | One-liner using a heavy dep. | Familiar to data folks. | Adds ~50 MB of wheels (pandas) or a Rust toolchain dep (polars) for a problem the 200-line stdlib `csv` module solves. Slow import. Pulls in numpy. Classic G2 / G4. | Rejected: violates D2 (minimality) and C-deploy simplicity; the stdlib already does R4. |
| Opt C: hand-roll a CSV parser | Write our own quote-state-machine. | No deps at all (not even pytest's csv awareness needed). | Re-implements RFC-4180 from scratch — bug farm for R4 (the exact thing the spec calls out). Stdlib `csv` is itself dep-free. | Rejected: more code, more bugs, no benefit over Opt A. |
| Opt D: defer / clarify | Ask the user 8 questions before coding. | Maximum certainty. | User said "one-off, no follow-up", pressed Enter, waiting. The spec is small and the assumptions (A1-A6) are cheap to document. | Rejected: clarification cost > implementation cost for this size of spec. |

Chosen option: A — stdlib only, single module, console-script entry point.
  - Satisfies R1-R6 because: `csv.DictReader` reads stdin as an iterator (R1, R2),
    yields a dict per row keyed by header (R2), handles quoted commas and `""`
    escapes per RFC-4180 (R4); `json.dumps(row, ensure_ascii=False)` + `\n` to
    `sys.stdout` produces JSON Lines (R3); a `[project.scripts]` entry in
    pyproject.toml installs `csv2jsonl` on PATH (R5); language is Python (R6).
  - Respects C-runtime (3.9+: csv, json, sys, argparse all stdlib),
    C-deploy (one wheel, no native code), C-storage (none),
    C-security (no network, no eval, no fs writes by tool itself),
    C-user (Python, minimal).
  - Simpler than alternatives because: zero runtime deps, ~30 lines of code,
    one source file. B adds a heavy dep. C reinvents stdlib. D delays.

MINIMAL ARCHITECTURE DECISION  (guards G1)
Modules / files to create:
| Module | Purpose | Discharges Rn / Cn / Initial-Contract | Why no smaller design suffices |
|---|---|---|---|
| `src/csv2jsonl/__init__.py` | Package marker; re-export `main` for `python -m`. | R5, C-deploy | Need a package to host the console-script and to be `pip install`-able. Could be flat single-file, but `src/` layout prevents accidental import-from-cwd test bugs and is the modern norm; cost is one empty file. |
| `src/csv2jsonl/__main__.py` | Allow `python -m csv2jsonl < input.csv` as fallback to the entry point. | R5 (alt invocation) | One line (`from . import main; main()`); makes the tool usable even before `pip install`. |
| `src/csv2jsonl/cli.py` | The whole tool: read stdin via `csv.DictReader`, write `json.dumps(row) + "\n"` to stdout, define `main()`. | R1, R2, R3, R4, IC1, INV1, INV2 | This IS the feature. Cannot be smaller than one function. |
| `tests/test_cli.py` | Pytest tests covering R1-R4 and edge cases (A3, A4). | NT1-NT5, D4 | Need at least one test file; combining all tests here is fine for a 30-line tool — splitting per requirement would be G1. |
| `tests/fixtures/` (inline strings, not files) | Test inputs as Python string literals passed via `io.StringIO`. | D4 | Avoids on-disk fixtures (smaller surface, no path issues). No file row needed — fixtures live inside the test module. |
| `pyproject.toml` | Project metadata, build backend (setuptools), Python version pin, console-script `csv2jsonl = "csv2jsonl.cli:main"`, optional `[project.optional-dependencies] dev = ["pytest"]`. | R5, R6, C-runtime, D4 | Required for `pip install .` and to put `csv2jsonl` on PATH. |
| `README.md` | Install + run + test commands a fresh clone would type. | D4 (run-instructions) | Needed for D4 reproducibility; ~20 lines. |
| `.gitignore` | Ignore `__pycache__/`, `*.egg-info/`, `dist/`, `build/`, `.pytest_cache/`. | (housekeeping; not a Rn) | Allowed under D2 because it prevents committing build artifacts that would later require a separate cleanup change; trivially small. |

Explicitly NOT created (would be G1/G6):
  - No `Reader`/`Writer`/`Formatter` classes — one function suffices.
  - No `config.py` — there is no configuration.
  - No `errors.py` — stdlib exceptions are fine.
  - No `logger.py` — a stdin/stdout filter should be silent on success.
  - No `setup.py` (pyproject.toml is the modern form).
  - No `tox.ini` / `noxfile.py` / CI config — user did not ask, single-Python-version
    project, can be added later if needed.
  - No `Dockerfile` — C-deploy is "pip install".

Dependencies to add:
| Dependency | Version | Why this exact dep | Could we do without? |
|---|---|---|---|
| (runtime) — none | — | Stdlib `csv`, `json`, `sys`, `argparse` cover R1-R5. | Yes — and we are. Zero runtime deps. |
| pytest (dev) | >=7,<9 | De-facto Python test runner; gives us `capsys` to capture stdout for NT-smoke and clean assert rewriting. | Yes (`unittest` is stdlib), but writing this with `unittest` adds ~15 lines of boilerplate (TestCase classes, `assertEqual`) for no benefit. pytest is a dev-only dep, never shipped to runtime. Justified under D2 because it discharges D4 (verifiable) at materially lower code cost than the stdlib alternative. |

(Every other dep that "would be without" — typer, click, rich, pydantic,
pandas, polars, orjson — is rejected. None are needed: argparse is stdlib
and we may not even need it; json is stdlib; csv is stdlib.)

INITIAL CONTRACTS AND INVARIANTS  (replaces brownfield's "preserve" with "establish")
IC1: `main(argv: list[str] | None = None, stdin=sys.stdin, stdout=sys.stdout) -> int`
     — Pre:  `stdin` is a text-mode iterable yielding CSV lines (RFC-4180-ish).
             `stdout` is a writable text stream.
             `argv` is None or a list of strings (if we add argparse for `--help`).
     — Post: For each data row in the CSV (rows after the header), exactly one
             line is written to `stdout`: a compact JSON object whose keys are
             the header cells (in header order is not guaranteed by JSON, but
             dict insertion order is preserved in Py3.7+, so keys appear in
             header order in practice) and whose values are the corresponding
             row cells as strings. Each line ends with `\n`. Returns 0 on
             success.
     — Errors: Returns non-zero (and writes a Python traceback to stderr) if
             the `csv` module raises, or if writing to stdout raises (e.g.
             EPIPE when downstream pipe closes — we should at minimum suppress
             BrokenPipeError quietly per the standard Python recipe).

IC2: Console-script entry point: `csv2jsonl = "csv2jsonl.cli:main"` in
     `[project.scripts]`. After `pip install .`, the shell command `csv2jsonl`
     invokes `main()` and uses its return value as exit code.
     — Pre:  `pip install .` (or `pip install -e .`) has been run in an env
             whose `bin/` is on PATH.
     — Post: `csv2jsonl < input.csv > output.jsonl` writes JSONL to
             output.jsonl and exits 0 on a well-formed CSV.

INV1: The tool never buffers more than one row in memory at a time
      (streaming). Enforcement: `csv.DictReader` is a generator; we iterate
      with `for row in reader: stdout.write(json.dumps(row) + "\n")`. No
      `list(reader)`, no `readlines()`. Will be enforced at
      `src/csv2jsonl/cli.py:main` (to be created).
INV2: The tool writes nothing to stdout other than JSONL lines (no banner,
      no progress, no logs). Errors / diagnostics go to stderr only. Enforcement:
      no `print` calls without `file=sys.stderr`; only `stdout.write(...)`
      writes to stdout, and only inside the row loop.
INV3: The tool reads nothing from stdin other than the CSV payload (no prompts,
      no interactive input). Enforcement: no `input()` calls anywhere.

CREATED SURFACE  (every file/artifact you'll create — guards D1, D2)
| File | Purpose | Discharges (Rn / Cn / IC / INV) |
|---|---|---|
| `src/csv2jsonl/__init__.py` | Package marker; `from .cli import main`. | R5, IC2 |
| `src/csv2jsonl/__main__.py` | `from .cli import main; raise SystemExit(main())`. | R5 (alt invocation `python -m csv2jsonl`) |
| `src/csv2jsonl/cli.py` | `main()` implementing the filter; the entire feature. | R1, R2, R3, R4, R6, IC1, INV1, INV2, INV3 |
| `tests/test_cli.py` | All pytest tests (NT1-NT5, NT-smoke). | D4, R1-R4, A3, A4 |
| `pyproject.toml` | Build metadata, Python pin, `[project.scripts] csv2jsonl = "csv2jsonl.cli:main"`, dev extras = pytest. | R5, R6, C-runtime, IC2, D4 |
| `README.md` | Install + invoke + test instructions a fresh clone would type. | D4 (run instructions) |
| `.gitignore` | Ignore Python build artefacts. | housekeeping (justified above) |

REQUIREMENT → CODE MAPPING  (after the plan; before commit)
R1 (read CSV from stdin)
  -> satisfied by `src/csv2jsonl/cli.py:main` reading from `sys.stdin`
     (passed in to `csv.DictReader`). Demonstrated by NT1 + NT-smoke.
  Inference type: pattern-reuse (stdlib `csv.DictReader` over a text iterator
  is the canonical pattern).

R2 (header row -> JSON keys)
  -> satisfied by `csv.DictReader` (no `fieldnames` arg means the first row
     is consumed as the header). Demonstrated by NT2.
  Inference type: pattern-reuse.

R3 (one JSON object per line, JSON Lines format)
  -> satisfied by `cli.py:main` writing `json.dumps(row, ensure_ascii=False) + "\n"`
     per row, no wrapping array. Demonstrated by NT3 (asserts each output line
     parses as JSON and the line count equals data-row count).
  Inference type: spec-decomposition (we decomposed "JSON Lines" into the
  three sub-properties: one object per line, trailing newline, no enclosing
  array).

R4 (quoted fields with embedded commas)
  -> satisfied by `csv.DictReader`'s default dialect = `excel`, which is
     RFC-4180-ish: handles `"a,b"` as one cell, `""` as escaped quote,
     quoted newlines. Demonstrated by NT4.
  Inference type: invariant-preservation of the stdlib parser's documented
  behaviour. ASSUMPTION: Python `csv` module's `excel` dialect handles
  RFC-4180 quoted-comma case as documented in the stdlib docs; verified
  by NT4 rather than by reading the C source.

R5 (invokable as `csv2jsonl < input.csv > output.jsonl`)
  -> satisfied by `[project.scripts] csv2jsonl = "csv2jsonl.cli:main"` in
     pyproject.toml; after `pip install .` the shell finds `csv2jsonl` on PATH.
     Demonstrated by NT-smoke (which does exactly that invocation via
     `subprocess.run(["csv2jsonl"], stdin=..., stdout=...)`).
  Inference type: pattern-reuse (standard Python entry-point mechanism).

R6 (Python is fine)
  -> satisfied by language choice. Demonstrated by the project running.

VERIFICATION SCAFFOLD  (guards G3, G5 — non-negotiable for greenfield)
Test framework choice: pytest >=7,<9. Chosen because it gives `capsys`
  (capture stdout/stderr) and `monkeypatch` (swap sys.stdin) with no
  boilerplate; tied to C-runtime (Python).
Smoke command (one command, real user-visible path):
  `printf 'a,b,c\n1,"x,y",3\n' | csv2jsonl`
  Expected stdout (exactly):
  `{"a": "1", "b": "x,y", "c": "3"}\n`
  This exercises R1 (stdin), R2 (header keys), R3 (one JSONL object), R4
  (quoted comma), R5 (invocation by name).
Build / type / lint commands:
  Build:  `python -m pip install -e ".[dev]"`
  Lint:   none configured (out of scope; user did not ask; would be G6).
  Types:  none configured (no mypy; same reason).
Fixture strategy: inline string literals in `tests/test_cli.py` fed to
  `io.StringIO` for unit tests of `main(stdin=..., stdout=...)`; for the
  smoke test, `subprocess.run(["csv2jsonl"], input=..., capture_output=True,
  text=True, check=True)` after install.
Run instructions (READMEable, exact commands a fresh clone would type):
  ```
  git clone <repo> && cd <repo>
  python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
  python -m pip install -e ".[dev]"
  pytest -q                                              # runs all tests, including smoke
  printf 'a,b,c\n1,"x,y",3\n' | csv2jsonl                # manual smoke, prints one JSONL line
  csv2jsonl < some_input.csv > some_output.jsonl        # canonical invocation from spec
  ```

NEW TEST OBLIGATIONS
NT1: `test_reads_stdin_and_uses_header_keys` — calls
     `main(stdin=StringIO("name,age\nAlice,30\nBob,25\n"), stdout=buf)`,
     asserts `buf.getvalue()` equals
     `'{"name": "Alice", "age": "30"}\n{"name": "Bob", "age": "25"}\n'`.
     Demonstrates R1 + R2 + R3.
     Runnable: `pytest -q tests/test_cli.py::test_reads_stdin_and_uses_header_keys`

NT2: `test_quoted_field_with_embedded_comma` — input
     `'a,b,c\n1,"x,y",3\n'`, asserts output is exactly
     `'{"a": "1", "b": "x,y", "c": "3"}\n'`.
     Demonstrates R4 (the spec-called-out case).
     Runnable: `pytest -q tests/test_cli.py::test_quoted_field_with_embedded_comma`

NT3: `test_jsonl_format_one_object_per_line_no_array` — feeds 3 data rows,
     asserts (a) `output.count("\n") == 3`, (b) every line parses with
     `json.loads`, (c) the output does NOT start with `[` and does NOT
     end with `]`.
     Demonstrates R3.
     Runnable: `pytest -q tests/test_cli.py::test_jsonl_format_one_object_per_line_no_array`

NT4: `test_edge_cases_empty_and_header_only` — (a) empty stdin -> empty
     stdout, exit 0; (b) header-only stdin -> empty stdout, exit 0;
     (c) row with embedded `\n` inside quotes parses as one row;
     (d) doubled `""` quote becomes a single `"` in the value.
     Demonstrates A3, A4, and the rest of R4.
     Runnable: `pytest -q tests/test_cli.py::test_edge_cases_empty_and_header_only`

NT5: `test_streams_does_not_slurp` — feeds an iterator that raises if
     `__next__` is called more than N+1 times for N rows actually read,
     verifying we don't call `list(reader)` somewhere. (Cheap proxy for INV1.)
     Runnable: `pytest -q tests/test_cli.py::test_streams_does_not_slurp`

NT-smoke: `test_smoke_installed_entry_point` — runs
     `subprocess.run(["csv2jsonl"], input='a,b,c\n1,"x,y",3\n',
     capture_output=True, text=True, check=True)`, asserts stdout equals
     `'{"a": "1", "b": "x,y", "c": "3"}\n'` and stderr is empty and
     returncode is 0. Skipped with a clear message if `csv2jsonl` is not
     on PATH (i.e. user ran `pytest` without `pip install -e .` first);
     README tells them to install first.
     Demonstrates R5 (the canonical invocation from the spec) end-to-end.
     Runnable: `pytest -q tests/test_cli.py::test_smoke_installed_entry_point`

(Every Rn is covered: R1->NT1; R2->NT1; R3->NT1+NT3; R4->NT2+NT4; R5->NT-smoke;
R6->the suite running on Python at all. There IS at least one NT-smoke.)

COUNTEREXAMPLE / SUFFICIENCY CHECK
For each Rn, soundness sketch (P(input)) or counterexample:

R1: P(input) = "for any text stream `s` of CSV bytes, main(stdin=s) consumes
    s as the input". Sketch: `csv.DictReader(s)` iterates s line-by-line until
    EOF; main passes sys.stdin (or a test StringIO). No counterexample known
    for well-formed text streams under A1 (UTF-8). Malformed encoding ->
    UnicodeDecodeError surfaces (acceptable per A6).

R2: P(input) = "first row's cells are the keys of every output object".
    Sketch: `csv.DictReader` (no `fieldnames=` arg) reads the first row as
    `fieldnames` (csv stdlib docs); each subsequent row is yielded as
    `dict(zip(fieldnames, cells))`. Counterexample concern: if the header
    row has duplicate column names, later wins, which silently drops a
    column. We document this under A3 / "limitations" rather than guard
    against it; the spec doesn't require uniqueness checks.

R3: P(input) = "for every CSV data row R there is exactly one line in
    stdout, that line is `json.dumps(dict_of_R) + "\n"`, and no other bytes
    are written to stdout". Sketch: the `for row in reader: stdout.write(...)`
    loop writes exactly one `json.dumps(row) + "\n"` per row; INV2 forbids
    other stdout writes. No counterexample.

R4: P(input) = "given RFC-4180-ish CSV, quoted fields containing `,`,
    `\n`, and `""` parse to the intended single string". Sketch: stdlib
    `csv` excel dialect has implemented this since Python 2; pinned by
    NT2 + NT4 against regressions in the parser (extremely unlikely).
    Counterexample concern: non-default dialects (tab-separated, custom
    quotechar) won't parse — but those aren't in scope (R4 says "commas",
    A1/A6 don't promise dialect detection).

R5: P(input) = "after `pip install .`, the shell command `csv2jsonl` runs
    main()". Sketch: setuptools writes a wrapper script in `<env>/bin/`
    (or `Scripts/` on Windows) per the `[project.scripts]` table; PEP 621
    standard. NT-smoke verifies end-to-end.

R6: Tautology — the implementation is in Python.

For each design decision, "could we satisfy with less?":
  - Single source file `cli.py`: could collapse into `__init__.py`. Slight
    win in file count, slight loss in import clarity (`csv2jsonl.cli:main`
    is a clear entry-point target). Net: keep, marginal call.
  - `__main__.py`: could remove and require `pip install`. Adds 2 lines,
    enables `python -m csv2jsonl` for users who haven't installed yet.
    Net: keep — discharges a real ergonomic case, costs nothing.
  - pytest: could use `unittest` (stdlib only). Saves one dev dep, costs
    ~15 lines of `class TestX(unittest.TestCase)` boilerplate and uglier
    failure messages. Net: keep pytest (dev only).
  - argparse / `--help`: could skip entirely. Spec doesn't ask. Net: skip
    initially; if added later, it's a 5-line change. Skipping satisfies G6.
  - `src/` layout vs flat layout: could put `csv2jsonl.py` at repo root.
    `src/` prevents the well-known footgun where tests accidentally import
    from cwd instead of the installed package. Net: keep `src/`; one extra
    directory for one real bug class avoided.

ADVERSARIAL CHECK  (must answer all three honestly)
1. Premature abstraction: any module/class/interface used in only one place?
   - `cli.main()` is one function, used by the entry point and by tests.
     Not an abstraction — it IS the feature.
   - No classes. No factories. No interfaces. No `Reader` / `Writer` /
     `Formatter`. Pass.
2. Unjustified dependency: would removing dep X mean writing >50 lines?
   - Runtime deps: zero. Nothing to remove.
   - pytest (dev): removing it costs ~15 lines of unittest boilerplate +
     manual stdout capture. <50 lines, so pytest is borderline
     over-refinement under the rule. Decision: keep it because it's
     dev-only (no shipped surface) and materially improves test
     readability; explicitly flagging this as the only judgement call.
3. Untestable boundary: can NT1-NT5 run with NO network, NO real DB, NO LLM?
   - Yes. NT1-NT5 use `io.StringIO` as a fake stdin and a `StringIO` as a
     fake stdout, calling `main(stdin=..., stdout=...)` directly. The
     fixture seam is the `stdin`/`stdout` parameters of `main()` —
     standard dependency-injection of the IO streams (IC1).
   - NT-smoke does need a real subprocess and PATH lookup — but it has no
     network, no DB, no LLM. It is skipped (with a clear message) if
     `csv2jsonl` isn't installed, so `pytest` on a fresh clone never
     spuriously fails before `pip install -e .[dev]`.

FORMAL CONCLUSION
By D1 (SUFFICIENT):           yes — every R1-R6 maps to at least one created
                              file and at least one NT.
By D2 (MINIMAL):              yes — zero runtime deps; one dev dep with
                              explicit borderline-justification; no
                              unmotivated module/class/file (G1/G2/G6 checked).
By D3 (INTERNALLY COHERENT):  yes — stdlib-only runtime, stdin/stdout text
                              I/O, streaming row-by-row, console-script
                              install, pytest harness; no contradictions.
By D4 (VERIFIABLE):           yes — `pytest -q` runs all NTs; NT-smoke runs
                              the literal user-spec invocation
                              `csv2jsonl < input.csv > output.jsonl` shape
                              via subprocess; README spells out the exact
                              fresh-clone commands.

Plan is READY TO IMPLEMENT: YES.
```
