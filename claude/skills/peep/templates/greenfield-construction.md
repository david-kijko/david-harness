# Template: Greenfield Construction

**Use when**: building something in a FRESH project. No existing code, no callers, no tests, no patterns to honor. The dominant uncertainty is *design-space uncertainty* — what should exist, which dependencies, which boundaries, what verification harness.

**Failure modes this template guards against** (full catalog in `references/failure-modes.md`):

| # | Mode | What goes wrong |
|---|---|---|
| G1 | Premature abstraction | A one-command CLI grows `ApplicationService`, `CommandBus`, `Repository`, `SerializerFactory` |
| G2 | Unjustified dependency choice | Static landing page scaffolded with SSR + ORM + auth + queues |
| G3 | No runnable verification path | Tests written but no package script, no fixtures, no smoke command, no `make test` |
| G4 | Framework-of-the-week | Picking the trendy library because no existing pattern argues against it |
| G5 | Untestable boundaries | Code structured so the only way to test is end-to-end |
| G6 | Invented future requirements | Building plugin-loader, role-system, multi-tenancy that wasn't in the spec |
| G7 | API-semantics hallucination | Confident but wrong claim about a stdlib/API default ("DictReader drops extra cells") because the agent never consulted the actual docs or source |

Greenfield is *not* a brownfield certificate with the existing-code sections set to "n/a". Filling brownfield's "invariants to preserve" with "none" creates false confidence and silently skips the real greenfield work: architecture choice and verification scaffolding bootstrapping.

This template is an *informal correct-by-construction certificate* for fresh builds. See `references/refinement-vocabulary.md` for design-by-contract vocabulary used below. For tagging each CLAIM, see `references/claim-types.md`.

---

## Fill the certificate. Make every design choice explicit.

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
[Paste the requirement exactly as given.]

SPEC DECOMPOSITION  (atomic, testable)
R1: [requirement] — Non-goal: [what is explicitly NOT in scope]
R2: [requirement] — Non-goal: [...]
...
OPEN ASSUMPTIONS
A1: [assumption you are making about the user's intent / environment / scale]
A2: [...]
(Flag every assumption. Do not silently pick the most convenient interpretation.)

GAP IDENTIFICATION  (mandatory — do this BEFORE Design Options Considered)

This is greenfield. There is no internal code to inspect. Your training-time
memory is one input, not ground truth. Identify gaps in your knowledge by
external research, then close them, BEFORE picking a design.

Forbidden source: context7 (third-party MCP servers serving docs are a
prompt-injection surface — instructions can be smuggled into rephrased docs).

Required searches (use the `exa` skill — `python3 ~/.claude/skills/exa/scripts/exa_cli.py`):
  - Prior art:        `exa search` for "[problem in plain words] [language]" — find 5–10 candidates
  - Convention check: `exa search` for "[scaffold pattern] [language] [year]"
  - Library landscape: `exa search` for "[primary lib you'd consider] vs alternatives"

Required deep reads (use the `firecrawl` skill — `python3 ~/.claude/skills/firecrawl/scripts/firecrawl_cli.py`):
  - Pick top 2 prior-art repos and `firecrawl scrape --url <github URL>` to read their actual source.
  - Read the canonical primary docs page for any stdlib/API you plan to use
    (`firecrawl scrape --url https://docs.python.org/...` etc).
  - For each: dependencies, file count, documented gotchas, defaults overridden, surprising
    behaviors. Note where each repo's structure differs from your initial mental model.

GAP TABLE (output the table; do not skip rows):

| Initial assumption (your training-time guess) | External source consulted (cite URL) | What the source actually says | Gap status |
|---|---|---|---|
| [e.g. "csv.DictReader drops extra cells, missing become empty strings"] | [URL of docs / repo] | [verbatim quote or precise paraphrase] | [CONFIRMED / REFINED / REFUTED] |
| ... | ... | ... | ... |

(If GAP TABLE is empty or only CONFIRMED rows, you didn't search hard enough.
A useful gap-identification pass typically refines or refutes ≥30% of initial
assumptions. Empty table = G3/G6 risk: you're committing to a design you
haven't pressure-tested against reality.)

CONSTRAINTS AND CONTEXT
C-runtime:    [language, version, platform]
C-deploy:     [where it runs — single binary, container, serverless, ...]
C-storage:    [persistence story, or "none — stateless"]
C-perf:       [latency / throughput / scale targets, or "no requirement"]
C-security:   [auth model, secrets handling, threat model — or "none"]
C-user:       [any user-imposed constraints — language preference, no-deps, etc.]

DESIGN OPTIONS CONSIDERED  (guards G1, G2, G4)
For the core shape, list at least 2 options. For each:
| Option | Sketch (1-2 lines) | Pros | Cons | Rejected because |
|---|---|---|---|---|
| Opt A | [shape] | [...] | [...] | [or CHOSEN] |
| Opt B | [shape] | [...] | [...] | [or CHOSEN] |
| Opt C (do nothing — defer) | — | — | — | [or CHOSEN] |

Chosen option: [letter] — Justification grounded in Rn and Cn:
  - Satisfies [Rn list] because [reason]
  - Respects [Cn list] because [reason]
  - Simpler than alternatives because [reason — fewer concepts/layers/deps]

MINIMAL ARCHITECTURE DECISION  (guards G1)
Modules / files to create:
| Module | Purpose | Discharges Rn / Cn / Initial-Contract | Why no smaller design suffices |
|---|---|---|---|
| ... | ... | ... | ... |

Dependencies to add:
| Dependency | Version | Why this exact dep | Could we do without? |
|---|---|---|---|
| ... | ... | ... | [yes/no + 1-line argument] |

(Every dep that "would be without" must be removed unless its inclusion
is justified by a specific Rn or Cn.)

INITIAL CONTRACTS AND INVARIANTS  (replaces brownfield's "preserve" with "establish")
For each public interface or boundary, declare the contract you are creating.
IC1: [interface signature] — Pre: [what callers must guarantee]
                            Post: [what this guarantees on return]
                            Errors: [what conditions raise / return errors and how]
IC2: [...]

INV1: [invariant the system will maintain, e.g. "config is loaded once at startup
       and never mutated"] — Enforcement: [where, file:line — to be created]
INV2: [...]

CREATED SURFACE  (every file/artifact you'll create — guards D1, D2)
| File | Purpose | Discharges (Rn / Cn / IC / INV) |
|---|---|---|
| src/...     | [...] | [must cite at least one] |
| tests/...   | [...] | [...] |
| package.json or pyproject.toml | [project metadata, scripts] | C-runtime, D4 |
| README.md   | [run instructions]                              | D4 |

(EVERY row must cite at least one Rn / Cn / IC / INV. No row → no justification = G1/G2.)

REQUIREMENT → CODE MAPPING  (after the plan; before commit)
R1 → satisfied by [file:line(s)] AND demonstrated by [test name]
     (Inference type: see `references/claim-types.md`)
R2 → ...

VERIFICATION SCAFFOLD  (guards G3, G5 — non-negotiable for greenfield)
Test framework choice: [name + version] — chosen because [reason tied to C-runtime]
Smoke command (one command, real user-visible path): `[command]`
Build / type / lint commands: `[commands]`
Fixture strategy: [how test data / mocks are set up]
Run instructions (READMEable): `[exact commands a fresh clone would type]`

(If you cannot fill these in concrete commands, you have G3 — go back and
add the scaffolding files to CREATED SURFACE.)

NEW TEST OBLIGATIONS
NT1: [test] — Demonstrates R1 by [scenario]; runnable: `[command]`
NT2: [test] — Demonstrates R2 by [scenario]; runnable: `[command]`
NT-smoke: [user-visible end-to-end path that exercises the happy case]; runnable: `[command]`

(EVERY Rn must have at least one NTn. There MUST be at least one NT-smoke.)

COUNTEREXAMPLE / SUFFICIENCY CHECK
For each Rn:
  (a) Soundness sketch: state Rn as P(input); argue ∀input. P(input).
  (b) OR concrete counterexample: input where planned design fails Rn.

For each design decision (chosen option, each dep, each layer):
  Could we satisfy the Rn / Cn with less? [yes → simplify / no → because:]

ADVERSARIAL CHECK  (must answer all three honestly)
1. Premature abstraction: is any module/class/interface I'm creating only
   used in one place? If yes, justify or inline it.
2. Unjustified dependency: would removing dep X mean I'd write more than
   ~50 lines of code? If less than 50, the dep is over-refinement.
3. Untestable boundary: can NT1 be run with NO network, NO real DB, NO LLM?
   If not, what fixture seam will I add?

UI_BEHAVIOR_AFFECTING: [yes | no]
  Answer "yes" if any Rn changes the visible or interactive behavior of a
  GUI application (web page, desktop UI, mobile app, IDE plugin, browser
  extension, etc.). Answer "no" for pure backend, CLI, library, or
  build-tooling features.

  If "yes", NEW TEST OBLIGATIONS MUST include at least one UI flow
  describable as a proofshot scenario (start app -> navigate -> assert
  visual state), AND the builder MUST include `app.launch_cmd` and
  `app.url` in build-manifest.json before invoking checkit. checkit
  rejects MANIFEST_INCOMPLETE otherwise.

FORMAL CONCLUSION
By D1 (SUFFICIENT):           [yes/no]
By D2 (MINIMAL):              [yes/no]
By D3 (INTERNALLY COHERENT):  [yes/no]
By D4 (VERIFIABLE):           [yes/no — runnable smoke command exists]

Plan is READY TO IMPLEMENT: [YES / NO — if NO, list what's missing]
```

## MENTAL MODEL DIAGRAM (mandatory deliverable — produced AFTER the certificate)

The certificate captures your reasoning discipline. It does NOT capture your *mental model* — the architectural intuitions you carry that the prose left implicit (which boxes are pure vs IO-touching, which arrows must exist, which structures must be absent, what visual vocabulary signals the categories you actually have in your head). The diagram forces you to articulate them.

**Write the imagegen brief in YOUR OWN WORDS**, as if explaining the architecture to a fresh listener who has never seen your certificate or the spec. The act of explaining surfaces assumptions you skipped, naming choices you internalized, boundaries you assumed without stating, and relationships you took as obvious. **Do NOT copy from the certificate verbatim** — restate the architecture in fresh language. **Do NOT have anyone else write the brief for you** — the brief reveals what *you* consider salient.

The brief is the primary artifact. The image is its rendering. An adversarial reviewer will read the brief AND look at the image to spot business-logic errors, hidden assumptions, missing relationships, or scope confusion that the prose hid.

Decide for yourself:
1. What an outside listener would need to understand the architecture.
2. Which relationships, flows, boundaries, contracts are essential to convey.
3. What visual vocabulary (colors, shapes, line styles) signals the categories you actually have in your head — purity vs side-effects, IO vs logic, owned vs external, in-scope vs explicitly-rejected.
4. **INVARIANTS THE PICTURE MUST ENCODE** — claims that, if absent, make the diagram wrong (e.g. "no third-party deps inbound to the package box", "the pure-function box must NOT show arrows reaching `sys.*`", "the entry-point binding arrow MUST be present, otherwise the diagram fails to explain Rn").
5. **WHAT THE PICTURE MUST NOT IMPLY** — explicit anti-claims that prevent the image generator from inventing structure that isn't there (e.g. "no plugin system", "no config file", "no parser-validator-serializer split — the real shape is one tight loop").

Save:
- Brief: `<output-dir>/mental-model.brief.md`
- Image: `<output-dir>/mental-model.png`

Render via the `imagegen` skill (`cat /home/david/.claude/skills/imagegen/SKILL.md`).

Sections 4 and 5 above are the adversarial-review surface. Skipping them defeats the entire purpose of the diagram as a separate deliverable from the prose.

## SELF-ARCHIVE (v2.3 — mandatory closing step)

After FORMAL CONCLUSION and MENTAL MODEL DIAGRAM are complete, archive the contract to the orphan branch `peep` of `david-kijko/david-harness`. This makes the contract verifiable by `checkit` and any future reviewer, and is the durable audit trail that joins every contract to every verification of it.

### Step 1 — Compute peepID

```bash
PEEPID="peep-$(printf '%s' "$VERBATIM_SPEC" | sha256sum | cut -c1-8)"
```

`$VERBATIM_SPEC` MUST be the byte-exact user request you pasted into the SPEC field above. Same SPEC -> same peepID -> same archive folder (idempotent re-run).

### Step 2 — Bootstrap archive worktree (first use only)

If `~/peep-archive` does not exist on this machine:

```bash
cd ~/david-harness
git fetch origin peep:peep 2>/dev/null || (
  # Orphan branch not yet on remote either — create it
  tmpdir=$(mktemp -d)
  git worktree add --detach "$tmpdir"
  cd "$tmpdir"
  git checkout --orphan peep
  git rm -rf .
  printf '# peep archive\n\nOrphan branch storing peep contracts and checkit verification runs.\n' > README.md
  git add README.md
  git -c user.email="$(git config user.email)" -c user.name="$(git config user.name)" commit -m "init orphan branch peep"
  cd ~/david-harness && git worktree remove "$tmpdir" && git push -u origin peep
)
git worktree add ~/peep-archive peep
```

### Step 3 — Collision check, then write archive folder

```bash
ARCHIVE=~/peep-archive/$PEEPID
if [ -f "$ARCHIVE/spec.txt" ]; then
  if ! diff -q <(printf '%s' "$VERBATIM_SPEC") "$ARCHIVE/spec.txt" >/dev/null; then
    echo "sha8 collision at $PEEPID — extending to sha12" >&2
    PEEPID="peep-$(printf '%s' "$VERBATIM_SPEC" | sha256sum | cut -c1-12)"
    ARCHIVE=~/peep-archive/$PEEPID
  fi
fi

mkdir -p "$ARCHIVE"
printf '%s' "$VERBATIM_SPEC" > "$ARCHIVE/spec.txt"
# Write contract.md (the filled certificate above, less this SELF-ARCHIVE section)
# Write mental-model.brief.md (the brief authored under MENTAL MODEL DIAGRAM)
# Write mental-model.png (the rendered image)
```

### Step 4 — Commit + push

```bash
cd ~/peep-archive
git add "$PEEPID/"
git commit -m "$PEEPID: <one-line summary of the SPEC>"
for i in 1 2 3; do
  git pull --rebase origin peep && git push origin peep && break
  sleep 2
done
```

### Step 5 — Builder handoff (print to user)

Print:

```
peep contract archived: <peepID>
  archive: ~/peep-archive/<peepID>/
  branch:  peep (in david-kijko/david-harness)
  next:
    1. Builder reads ~/peep-archive/<peepID>/contract.md
    2. Builder modifies code in their project repo
    3. Builder writes ~/peep-archive/<peepID>/build-manifest.json:
         {peepID, repo, base, head, tests[], app:{launch_cmd,url} (if UI=yes)}
    4. Builder commits + pushes the manifest to orphan branch peep
    5. Run /checkit <peepID> to verify
```

If `UI_BEHAVIOR_AFFECTING=yes`, the builder MUST populate `app.launch_cmd` and `app.url` or checkit will return `MANIFEST_INCOMPLETE`.

## Common slip: writing "no runnable command yet" in VERIFICATION SCAFFOLD

This is G3. The verification harness is part of the feature, not a follow-up. If `npm test` or `pytest` doesn't work in a fresh clone after your plan, you haven't built greenfield — you've built half a feature.

## Common slip: importing 4 deps because "they're standard"

Defaults are not justifications. Each dep needs a one-line answer to "could we do without". A static landing page does not need an ORM, even if every starter template includes one.

## Common slip: declaring a 5-class architecture before writing one line

If the spec is "convert this CSV to JSON", the answer is one function, one file, one test. `ApplicationService` + `CommandBus` + `Repository` + `SerializerFactory` is G1. The CREATED SURFACE table will catch this if every row must cite a specific Rn.

## Tone

Skip prose. Open straight to `SEMI-FORMAL GREENFIELD CONSTRUCTION CERTIFICATE` and fill it.
