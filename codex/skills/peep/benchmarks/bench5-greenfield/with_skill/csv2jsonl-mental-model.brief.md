# csv2jsonl — Architecture Diagram Brief

## What the image needs to communicate

This is a tiny Unix-pipeline CLI tool. The whole reason it exists is so a user can type `csv2jsonl < input.csv > output.jsonl` and get one JSON object per CSV row on stdout. The diagram should make that pipeline obvious at a glance, then reveal the small Python package that sits between the two pipes, then surface the four or five non-obvious stdlib defaults that I had to override to make the tool behave correctly.

A reader looking at the picture should walk away knowing:

1. The data path is **stdin -> Python package -> stdout**, with two filesystem files (`input.csv`, `output.jsonl`) bracketing the whole thing only because the shell redirected them in.
2. The Python package has **two source files with logic** (`_core.py` and `cli.py`) plus an `__init__.py` re-export, registered as a console script via `pyproject.toml`. It is **stdlib-only** at runtime.
3. There are **specific non-default knobs** on the stdin reader, the CSV parser, and the JSON writer that prevent silent-corruption bugs. These knobs are the "real" content of the design — the rest is wiring.
4. There are **two error exits** (data error -> 1, usage error -> 2) and **one swallowed signal** (BrokenPipeError -> 0).
5. Tests come in **two flavors**: in-process unit tests that call `convert()` directly with `io.StringIO`, and one subprocess smoke test that runs the installed `csv2jsonl` binary on PATH.

Everything else (README, .gitignore, the spec itself) is supporting cast and should be visually demoted.

## Layout

Use a **landscape canvas, roughly 16:10**. The eye should travel **left to right** along the data flow. Stack supporting context above and below the main flow.

### Top band — the user-visible invocation (thin strip across the top)

A monospaced terminal-style strip with the literal text:

```
$ csv2jsonl < input.csv > output.jsonl
```

This is the **promise**. Everything below the strip is how the promise is kept. Render it on a dark terminal-green background with a subtle prompt glyph.

### Middle band — the data pipeline (the dominant 60% of the canvas)

Three big blocks, left to right, connected by thick arrows:

**Block 1 (far left): `input.csv` file icon.** Document-with-corner-fold shape, label "input.csv", small caption underneath: "UTF-8, may have BOM, may have embedded newlines in quoted fields". Color: neutral grey-blue (it's just data, not our code).

**Arrow 1: stdin pipe.** A thick arrow labeled `< stdin` with a small annotation hovering over it: `io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8-sig", newline="")`. The annotation should be in a callout bubble, slightly off the arrow, in a warning-yellow tint to signal "this is a non-default choice that matters".

**Block 2 (center): the Python package.** This is the centerpiece. Render it as a rounded rectangle labeled `csv2jsonl/` (Python package). Inside it, three stacked sub-boxes top to bottom:

  - `cli.py — main()` (top sub-box). Caption: "argv check, SIGPIPE -> SIG_DFL, rebind stdin, catch errors, set exit code". Color this sub-box a **slightly warm orange** to signal "I/O wiring, not logic".
  - `_core.py — convert(in, out) -> int` (middle, largest sub-box). Caption: "the only file with real logic; ~25 LOC". Color this sub-box a **cool teal** to signal "pure function, easy to test". Inside this sub-box, draw a tiny inner loop arrow with the legend: `for row in DictReader: out.write(json.dumps(row) + "\n")`. Also include a small badge that says `RowError` (a custom exception subclass) attached to this box.
  - `__init__.py` (bottom, thin sub-box). Caption: "re-exports `convert`, `RowError`". Same teal as `_core.py` but lighter / more washed out — it's a one-liner.

To the **right edge of the package box, attached like a flag**, draw a small purple tag labeled `pyproject.toml` with caption: `[project.scripts] csv2jsonl = "csv2jsonl.cli:main"`. The tag should have a small arrow pointing back at `cli.py:main` to show the entry-point binding. This is what puts the binary on `PATH`.

**Arrow 2: stdout pipe.** A thick arrow labeled `> stdout`. Annotation callout (warning-yellow again): `json.dumps(row, ensure_ascii=False) + "\n"` — emphasize the `\n` (LF, not CRLF) and the `ensure_ascii=False` (UTF-8 passthrough, not `\uXXXX`).

**Block 3 (far right): `output.jsonl` file icon.** Same document shape as `input.csv` but with a small label inside it showing two example lines:

```
{"name": "Ada", "city": "Lon,don"}
{"name": "Grace", "city": "NYC"}
```

Caption underneath: "one JSON object per line, LF-terminated, UTF-8".

### Lower-left cluster — the non-default knobs (the "gotchas" panel)

A boxed panel titled **"Stdlib defaults we had to override"** with four short rows. Each row has a small icon (a wrench or gear), the knob, and the bug it prevents. Use a soft red-pink background to signal "danger averted":

  1. `encoding="utf-8-sig"` -> strips Excel's UTF-8 BOM so the first header key isn't `"﻿name"`.
  2. `newline=""` -> preserves embedded newlines inside quoted CSV fields (csv module requirement).
  3. `restkey=<sentinel>` + raise `RowError` -> rejects rows with extra cells instead of stuffing them under a `None` key that JSON-serializes to `"null"`.
  4. `restval=""` -> missing cells become `""` not JSON `null`, so "missing" doesn't get conflated with "explicit null".
  5. `ensure_ascii=False` on `json.dumps` -> non-ASCII characters pass through as UTF-8 bytes.
  6. `signal(SIGPIPE, SIG_DFL)` on POSIX -> `csv2jsonl < big.csv | head` exits cleanly instead of dumping a `BrokenPipeError` traceback.

Six rows; group as a single visual unit. The point of this panel is to show the reader: **the bytes-in-bytes-out arrow looks trivial, but it isn't — these six knobs are the design.**

### Lower-right cluster — exit codes

A small traffic-light style legend titled **"Exit codes"**, three rows:

  - **0 (green)**: success, OR caller closed the pipe (BrokenPipeError swallowed).
  - **1 (red)**: data error — malformed CSV, row with extra cells (`RowError`), unicode decode error.
  - **2 (amber)**: usage error — any argv beyond the program name.

### Lower-center cluster — the test surface

Below the main pipeline, a horizontal strip titled **"Verification"** with two grouped boxes side-by-side:

  - **Left box: `tests/test_convert.py`** — caption "in-process; feeds `io.StringIO` into `convert()`; covers basic rows, quoted-comma, doubled-quote escape, unicode passthrough, empty/header-only input, row length mismatch (NT1–NT6)". Color: light teal (matches `_core.py` — same code path).
  - **Right box: `tests/test_cli_smoke.py`** — caption "subprocess; runs `csv2jsonl` on PATH after `pip install -e .[dev]`; the only test that proves R4". Color: light orange (matches `cli.py`).

Connect each test box to the package sub-box it exercises with a thin dashed line, to make the "what tests what" relationship visible.

### Top-right corner — the spec lineage (small, demoted)

A small grey sticky-note style box in the upper-right corner titled **"Spec -> Requirements"** listing R1..R5 in one line each (read CSV from stdin; one JSON per row with header keys; RFC-4180 quoting; invocable as `csv2jsonl < in > out`; JSONL convention). Render small and muted — it's there for traceability, not as the focal point.

### Top-left corner — what we explicitly didn't build (also small, demoted)

A matching grey sticky-note titled **"Rejected"** with one-line items: no Click/Typer (zero flags); no csvkit/agate dep (heavyweight, defeats the point); no single-script-at-repo-root (no clean install path); no type inference (`"3"` stays a string, pipe to `jq` if you want a number); no Makefile / tox / pre-commit / Dockerfile (none asked for).

These two corner notes balance the composition and tell the reviewer "we considered alternatives and said no on purpose."

## Visual vocabulary

- **Cool teal**: pure-function code that is easy to test (`_core.py`, `__init__.py`, the unit-test box).
- **Warm orange**: I/O wiring code that touches the OS (`cli.py`, the subprocess smoke test).
- **Purple**: packaging / installation metadata (`pyproject.toml`, the `[project.scripts]` binding).
- **Neutral grey-blue**: opaque data files we don't own (`input.csv`, `output.jsonl`).
- **Warning yellow**: non-default knobs and overrides applied at I/O boundaries (the callouts on the stdin and stdout arrows).
- **Soft red-pink**: the "stdlib defaults we had to override" panel — averted bugs.
- **Terminal green**: the literal shell invocation strip across the top.
- **Muted grey**: spec/requirements and rejected-options corner stickies.

Arrow conventions:
- **Thick solid arrows**: data flow (CSV bytes -> dict -> JSON bytes).
- **Thin solid arrow**: code reference (the `pyproject.toml` tag pointing at `cli:main`).
- **Dashed lines**: test-to-code-under-test relationships.

Typography: monospace for file names, function signatures, code snippets, and shell commands. Sans-serif for captions and section titles.

## Invariants the picture must encode (otherwise it's wrong)

- The data flow is **strictly streaming** — there is no accumulator, no `list(reader)`, no buffer. Make this visible by drawing the inner-loop arrow inside `_core.py` rather than any "queue" or "buffer" shape.
- `convert()` is **pure of `sys.*`** — it takes streams as arguments. The picture must NOT show `_core.py` reaching out to `sys.stdin`. Only `cli.py` touches `sys.*`.
- The console-script binding is the **only** thing that makes `csv2jsonl < ...` work at the shell. The arrow from `pyproject.toml` to `cli.py:main` must be present, or the diagram fails to explain R4.
- There are **zero runtime dependencies**. The package box should have no inbound arrows from any third-party library node. Pytest exists, but only as a dev-dep — show it (if at all) only inside the Verification strip, not as a runtime dependency of the package.
- The smoke test is the **only** test that proves the spec-literal invocation works. The dashed line from `test_cli_smoke.py` should land on `cli.py` AND on the `pyproject.toml` tag, not on `_core.py`.

## What the picture must NOT imply

- No database, no network, no auth, no config file, no logging system, no plugin system, no async, no threads. If the renderer is tempted to add a "Config" box or a "Logger" box or a "Cache" box, it is wrong — none of those exist.
- No "parser -> validator -> serializer" three-stage pipeline inside the package. The real shape is one tight `for` loop. Keep it honest.
- No file-system fixtures in the test boxes. Tests use in-memory `StringIO` and subprocess stdin; do not draw a "fixtures/" folder.

## Tone

Clean, technical, slightly playful in the way good architecture diagrams are. Think "Julia Evans zine page" energy: confident labels, plenty of breathing room, color used to convey meaning rather than decoration. Avoid 3D effects, drop shadows beyond a subtle one, and gradients beyond flat tints. White or very light off-white background everywhere except the terminal strip and the colored sub-boxes.

Aspect ratio target: roughly 1600x1000. No watermark, no extra branding, no logos.
