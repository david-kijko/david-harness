# checkit — Architecture Diagram Brief

## What this image must communicate

I am drawing a system that closes a verification loop in three stages —
**plan, build, audit** — and persists a permanent, diffable trail of every
contract and every audit so that nothing the builder shipped is taken on
trust ever again. A reader who sees this diagram should walk away knowing:

1. The **peep** skill produces a contract at *plan time* — a structured
   document plus a hand-authored architecture image. That contract is the
   source of truth.
2. A **builder agent** (separate session, separate skill, possibly a
   different model entirely) implements the feature in the project repo.
3. The **checkit** skill is invoked at *audit time* and is given the
   contract, the architecture image, and the builder's diff. It does
   something unusual: before it ever looks at the contract's architecture
   image, it produces its own architecture image *from the diff alone* —
   a blind reconstruction. Only after that blind drawing exists does it
   line the two images up and look for gaps.
4. All three stages share one piece of glue — the **peepID**, a
   deterministic hash of the verbatim SPEC. Same SPEC, same peepID, same
   archive folder. The peepID is the foreign key joining contract,
   architecture, builder diff, and verification.
5. The archive lives on an **orphan branch `peep`** in the david-harness
   GitHub repo, checked out as a sibling worktree at `~/peep-archive/`.
   Nothing in this branch shares history with the skill source code on
   `main`. Each commit is a contract or a verification run.

The diagram should make the **blind-reconstruction firewall** the most
visually striking element on the canvas. Everything else is wiring; that
firewall is the design's load-bearing wall.

## Layout

Landscape canvas, ~16:10. Three horizontal bands stacked top to bottom.
The peepID glue thread runs vertically down the center as a labeled spine,
binding all three bands.

### Top band — PLAN time (peep)

Left to right:

- **User's plan.md** — document icon, neutral grey-blue, captioned "raw
  feature spec".
- Thick arrow into a rounded rectangle labeled **`peep` skill**, colored
  in the cool teal we use for analytical/discipline skills. Inside this
  rectangle, three sub-elements stacked vertically:
  - top sub-box: "SPEC decomposition (R1..Rn)"
  - middle sub-box: "Brownfield/Greenfield certificate"
  - bottom sub-box: "MENTAL MODEL DIAGRAM (brief + image)"
- Out the right side, two arrows fan out to two artifact icons:
  - **contract.md** (markdown document icon, teal tint)
  - **mental-model.png** (image icon, teal tint with a small picture-frame
    glyph)

A short downward arrow from the peep box, **labeled with the peepID**
(rendered as `peep-bbfa2319` literally), drops into the central spine.
This is the moment peepID is computed: `sha8(verbatim SPEC)`. Annotate
the arrow with `sha256(SPEC)[0:8]` so the reader sees the formula.

A small purple flag attached to the peep box: **"v2.3: self-archive"** —
this signals the new behavior added by this design.

### Middle band — BUILD time (builder agent)

This band is intentionally **less detailed** than the peep and checkit
bands. The diagram is *not* about how the builder works; it's about how
checkit verifies the builder. Show:

- The same peepID spine descends into this band on the left side.
- A rounded rectangle labeled **builder agent** in warm orange (the
  "I/O wiring, side-effects" color from the peep palette). Caption:
  "writes/edits files in the project repo".
- An icon labeled **project repo** (folder icon, generic) to the right
  of the builder. The arrow from builder to repo is thick and labeled
  `git diff = the slice checkit will audit`.
- A small dashed line from the contract.md artifact (top band) into the
  builder, captioned "contract is the spec the builder implements".

The builder's box should look slightly faded — it's not the focus, and
the diagram should communicate "checkit doesn't trust this; that's why
it exists".

### Bottom band — AUDIT time (checkit)

This is the visual climax. Use about 45% of the canvas for this band.

The peepID spine arrives at the left as a labeled bar. From it, two
inputs flow into checkit:

- the **contract.md** (re-fetched from the archive — same file, same SHA)
- the **builder's diff** (from the project repo)

Notably absent from the inputs into checkit's first phase: the
**mental-model.png**. Draw an actual visual gap here — the image icon
is greyed out and labeled **"sealed until phase 2"**. This is the
firewall.

Inside the checkit box (which should be the largest box on the canvas),
two phases are drawn left-to-right with a **vertical wall** dividing
them. The wall is labeled **"BLIND RECONSTRUCTION FIREWALL"** in red
caps.

**Phase 1 (left of wall):**
- Sub-box "Forensic reconstruction" — receives only contract + diff.
- Inner arrow: "diff → grep, trace, model".
- Output: two artifacts on the wall side — `actual-architecture.brief.md`
  and `actual-architecture.png`. These are produced *blind*.

**Phase 2 (right of wall):**
- The wall has a one-way arrow: `phase 1 outputs → phase 2 inputs`.
- A new sub-box "Architectural gap analysis" receives both architectures
  side by side: peep PNG (now allowed in) and the actual PNG (just
  produced). Caption: "side-by-side visual diff".
- Below it, a sub-box "Behavioral validation (proofshot)" — conditional;
  greyed out unless the contract's CHANGE SURFACE includes a frontend
  file. Arrow into a small browser icon labeled "proofshot session".
- Right edge: produces three artifacts:
  - `gap-report.md` (markdown icon, salmon-pink tint to signal "issues")
  - `verdict.md` — rendered as a small traffic-light strip with the six
    rungs visible: PERFECT (green), VERIFIED (green-yellow), ARCH_GAP
    (yellow), LOGIC_GAP (orange), BEHAVIORAL_FAIL (red-orange), FAILED
    (red). Highlight the rung the verdict falls on (use a generic
    "ARCH_GAP" highlight in the example diagram).
  - `corrective-prompt.md` — appears only on the three failing rungs;
    drawn dashed/conditional with caption "only when verdict ∈ {LOGIC_GAP,
    BEHAVIORAL_FAIL, FAILED}".

### The spine — peep-archive on orphan branch `peep`

Down the left edge of the canvas, draw a vertical labeled **bar** titled
**`~/peep-archive/peep-bbfa2319/`** (use a real peepID for concreteness).
Inside this bar, a stacked file tree visible:

```
spec.txt
contract.md
mental-model.brief.md
mental-model.png
checkit/
  run-1/
    actual-architecture.brief.md
    actual-architecture.png
    gap-report.md
    verdict.md
    corrective-prompt.md   (conditional)
    proofshot/             (conditional)
```

Above this file tree, a small **GitHub octocat icon** with a label
**"orphan branch `peep`"** and an arrow showing automatic push.

Connect:
- top band's contract.md and mental-model.png artifacts → archive bar
  (arrow labeled "peep self-archives, push")
- bottom band's checkit/run-N/* artifacts → archive bar (arrow labeled
  "checkit self-archives, push")

This makes the archive visually the spine that holds everything together.

## Visual vocabulary (must match peep's palette for consistency)

- **Cool teal**: pure analysis/discipline (peep, peep artifacts, checkit's
  reconstruction phase).
- **Warm orange**: side-effecting wiring (builder agent, proofshot session).
- **Purple**: packaging / version metadata (the "v2.3 self-archive" flag,
  the symlink-to-harness annotation if shown).
- **Neutral grey-blue**: opaque user data (plan.md, project repo).
- **Salmon pink**: gap/failure artifacts (gap-report.md, the failing
  verdict rung).
- **Red caps**: the firewall label.
- **Verdict ladder**: green → green-yellow → yellow → orange → red-orange
  → red (left-to-right rungs).

Arrow conventions:
- Thick solid: data flow.
- Thin solid: same-data re-read (e.g. contract.md re-fetched by checkit).
- Dashed: conditional artifact (corrective-prompt, proofshot).
- One-way arrow through the firewall: phase 1 outputs → phase 2 inputs.

Typography: monospace for filenames, peepIDs, SPEC tokens, command names.
Sans-serif for box labels and annotations.

## INVARIANTS THE PICTURE MUST ENCODE

- The **firewall** must be drawn as an actual visual barrier — not
  implied by ordering. Without it the diagram fails to communicate the
  one structural decision that makes blind reconstruction enforceable.
- The **mental-model.png artifact must be visually sealed/greyed in
  checkit phase 1**. If the rendered image shows it as an input there,
  the diagram is wrong.
- The **peepID label** must appear at three points: (1) where it's
  computed from SPEC, (2) on the archive bar, (3) at the input to
  checkit. This proves it is the joining key.
- The **archive bar** must show BOTH the peep artifacts AND the checkit
  artifacts in the same folder. They share the peepID; they share the
  folder.
- The **GitHub push arrow** must originate from the archive bar, not
  from the peep or checkit boxes directly. The archive is the only thing
  that talks to the remote.
- The **verdict ladder** must show all six rungs with the correct
  ordering and color progression (green → red).

## WHAT THE PICTURE MUST NOT IMPLY

- No direct arrow from peep skill → builder agent. peep produces a
  contract; the builder reads the contract from the archive. Drawing
  a peep → builder arrow would suggest tight coupling that doesn't exist.
- No edits to the project repo by checkit. Checkit is read-only against
  the project; it only writes into the archive. If the diagram shows a
  write arrow from checkit into the project repo, it is wrong.
- No checkit access to mental-model.png in phase 1. Already covered by
  the firewall, but worth restating: any line crossing the firewall
  from peep PNG into phase 1 is a bug in the diagram.
- No `~/.codex/skills/checkit/` mirror. checkit is Claude-only this round
  per user decision. Do NOT draw a Codex-side mirror.
- No counter file or central registry for peepIDs. The peepID is
  derived from content; there is no `next-id.txt` or similar. If the
  diagram shows a counter, it is wrong.
- No automatic builder-trigger from a failed verdict. Corrective-prompt.md
  is a *file produced for the next builder session* — not an automated
  re-dispatch. Do not draw an arrow from corrective-prompt back into the
  builder agent.
- No NotebookLM, no MCP servers, no database, no message queue. The
  whole pipeline is files + git. Keep it that way.

## Tone

Clean, technical, slightly playful where the verdict ladder is concerned
(it benefits from a real traffic-light feel). Same energy as the peep
v2-architecture.png and the csv2jsonl mental-model.png — confident
labels, breathing room, color used semantically. Avoid 3D effects,
gradients, or decorative shadows. White or near-white background
everywhere except the firewall band (subtle red wash) and the verdict
ladder cells.

Aspect ratio: roughly 1600×1000. No watermark, no extra branding.
