# Greenfield 3-Way Ablation — Hephaestus Verdict

## Ranking
1. B — SKILL+TOOLS
2. A — BASELINE
3. C — TOOLS-ONLY

## A vs B (baseline vs skill+tools)
- Better: B
- Discriminating finding: B is materially better because it verifies and corrects a concrete stdlib gotcha: `with_skill/output.md:100` says default extra CSV fields become a `None` key that JSON-serializes as `"null"`, while A both chooses a softer `_extra` behavior and incorrectly claims `json.dumps` would refuse it at `baseline/output.md:50`.

## A vs C (baseline vs tools-only)
- Better: A
- Discriminating finding: A is materially better on scope discipline because it keeps the project to `README.md`, `pyproject.toml`, package files, tests, and `.gitignore` at `baseline/output.md:66-77`, while C adds unasked surface area including `LICENSE`, `.python-version`, `conftest.py`, committed fixture files, `ruff`, help/version, and a slow RSS test at `tools_only/output.md:52-75`, `tools_only/output.md:80`, and `tools_only/output.md:125-126`.

## B vs C (skill+tools vs tools-only)
- Better: B
- Discriminating finding: B keeps the researched gaps tied to explicit requirements and rejects nonessential project machinery — `with_skill/output.md:160-161` says no Makefile/tox/pre-commit/GitHub Actions/Docker because none discharge an Rn — while C uses the same general research signal but still grows the project with `ruff`, fixtures, help/version, and a slow benchmark at `tools_only/output.md:80` and `tools_only/output.md:121-126`.

## Value decomposition
B's improvement over A is mostly tool-driven for factual gap identification, but the certificate is carrying nontrivial scope-control and handoff-readiness weight. Rough split: 65% tools, 35% certificate. The tool-derived wins are visible in B's gap table: verified `DictReader` extra-field behavior (`with_skill/output.md:100`), missing-cell `restval=None` behavior (`with_skill/output.md:101`), `ensure_ascii=True` default (`with_skill/output.md:102`), BOM corruption (`with_skill/output.md:104`), and BrokenPipe behavior (`with_skill/output.md:105`). C achieves much of that same gap-identification benefit without the certificate: it identifies stdlib CSV as sufficient (`tools_only/output.md:32`), UTF-8/JSONL constraints (`tools_only/output.md:16-17`), ragged-row handling (`tools_only/output.md:20`), BOM handling (`tools_only/output.md:118`), and BrokenPipe handling (`tools_only/output.md:22`). But C loses the structure benefits: it is less minimal, less auditable about which research was actually run, and introduces a questionable malformed-input/surrogateescape policy (`tools_only/output.md:16`, `tools_only/output.md:85-92`) that conflicts with a clean UTF-8 JSONL contract.

## Implication for skill design
Do not drop the greenfield certificate path. C proves that exa/firecrawl can recover many of the factual gaps, but B proves the certificate is useful for forcing requirement mapping, explicit non-goals, and minimality checks. Recommendation: keep skill+tools as the greenfield path, but reduce output overhead by making the full certificate an internal worksheet and emitting a compact handoff plan plus a short gap table. The heavy 474-line certificate should not be the default deliverable unless the user asks for the full proof artifact.

## Cost analysis
- A tool-use count (rough): 0 visible external tools; 243 output lines.
- B tool-use count (rough): 5 exa searches (`with_skill/output.md:68-78`), 4 firecrawl/deep reads (`with_skill/output.md:80-86`), and 4 local Python runtime checks (`with_skill/output.md:88-95`); 474 output lines.
- C tool-use count (rough): not auditable from the answer; visible citations/research anchors include Python CSV docs and CPython source (`tools_only/output.md:32`), JSONL/NDJSON specs (`tools_only/output.md:16-17`), and packaging entry-point docs (`tools_only/output.md:80`); 193 output lines.
- Scope-creep observations per condition:
  - A: Moderate test breadth (16 tests, including optional installed-script and BrokenPipe tests at `baseline/output.md:181-188`) but mostly tied to the CLI contract; no runtime dependency creep.
  - B: Major token/certificate overhead and one arguably overformal custom `RowError` surface (`with_skill/output.md:186-188`, `with_skill/output.md:405-417`), but strong discipline against unrelated tooling (`with_skill/output.md:160-161`).
  - C: Lowest answer-token cost, but highest implementation-scope creep: extra repo files/fixtures (`tools_only/output.md:52-75`), `ruff` (`tools_only/output.md:80`, `tools_only/output.md:152-153`), help/version behavior despite no flags in the spec (`tools_only/output.md:34`, `tools_only/output.md:126`), and an opt-in slow RSS test (`tools_only/output.md:125`).
