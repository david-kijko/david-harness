# checkit — Flow Diagram (sequence, not architecture)

## What this image must communicate

Time flows **left to right**. Four actors on horizontal swim-lanes (top to
bottom): **USER**, **peep skill**, **builder agent**, **checkit skill**. A
fifth lane sits at the bottom as a horizontal bus: **orphan branch `peep`
at ~/peep-archive/**, the persistent log every other lane writes to.

The diagram is a **sequence diagram with swim lanes**, not an architectural
infographic. A reader should be able to put their finger on the leftmost
event and trace the entire system rightward in time, watching artifacts
appear and pass between lanes.

The single hardest thing to communicate is **the sealed temp dir** in the
checkit lane. That box is the enforcement mechanism. It must be the visual
peak of the diagram.

## Layout

Landscape, ~16:10. White background. Four swim lanes stacked vertically
across the middle 75% of the canvas, with a thinner orphan-branch bus lane
across the bottom 15%. A thin time-axis bar across the very top labeled
**"time →"** with tick marks at T0–T13 (the events I'll number below).

Each lane is a horizontal strip with the actor name in a coloured tag on
the left edge:
- **USER** — neutral grey-blue tag
- **peep skill** — cool teal tag (analytical/discipline)
- **builder agent** — warm orange tag (side-effecting/IO)
- **checkit skill** — cool teal tag with a thin red border (auditor)
- **orphan branch peep** — purple tag (storage/versioning)

Inside each lane, events are drawn as small rounded boxes anchored at their
T-tick on the time axis. Artifacts produced or consumed at an event are
small file icons next to the box. **Vertical arrows** drop from a
producer-event in one lane down to the orphan-branch bus to indicate
"committed and pushed at this moment". **Horizontal arrows** within a lane
indicate "the same actor moves to its next step". **Diagonal arrows
between lanes** indicate "actor A produced something actor B now consumes",
labeled with the artifact name.

## The sequence (left to right)

### T0 — USER lane
- Box: "USER writes plan.md and invokes peep on it".
- Artifact: `plan.md` icon.
- Arrow: diagonal down-right into peep lane.

### T1 — peep lane
- Box: "peep fills SEMI-FORMAL certificate".
- Box (immediately after): "peep computes **peepID = sha8(SPEC)**".
  Render the formula literally: `sha256(SPEC)[0:8]`.
- Box (immediately after): "peep writes archive folder".
- Artifacts emerging right of these boxes:
  `spec.txt`, `contract.md`, `mental-model.brief.md`.
- Box (last in T1): "peep calls **/imagegen** → hephaestus → Codex
  `image_gen`". Render this as a small dispatch arrow leaving the lane and
  returning with a `mental-model.png` artifact.
- Drop arrow to bus: vertical thick arrow from the artifacts down to the
  orphan-branch bus, labeled **"git commit + push (orphan branch peep)"**.

### T2 — USER lane
- Box: "USER hands the contract to a builder agent".
- Arrow: diagonal down-right into builder lane, carrying the
  `contract.md` artifact (re-read from the archive bus, *not* from peep
  directly — show the arrow originating from the bus, going up into
  builder's T2 box).

### T3 — builder lane
- Box: "builder modifies code in their project repo".
- Show a separate small icon outside the swim-lane structure: a generic
  **project repo** folder, sitting to the right of the builder lane,
  labeled `<some repo path>`. The builder's box has a fat arrow into this
  repo icon labeled `git commit (in the project repo, NOT the orphan
  branch)`.
- Box (immediately after): "builder writes **build-manifest.json**" —
  this is the new artifact that hephaestus's adversarial review surfaced
  as the missing piece. Caption underneath the artifact:
  `{peepID, repo, base, head, untracked_policy, tests, app:{launch_cmd, url}}`.
- Drop arrow to bus: vertical arrow from `build-manifest.json` down to
  the orphan-branch bus, labeled **"git commit + push (orphan branch
  peep, archive folder peep-bbfa2319/)"**.

### T4 — USER lane
- Box: "USER invokes `/checkit <peepID>`" — render literally with a
  monospaced terminal strip.
- Arrow: diagonal down-right into checkit lane.

### T5 — checkit lane
- Box: "checkit reads `build-manifest.json` from the bus".
- Arrow: vertical UP from the orphan-branch bus into checkit's T5 box,
  carrying `build-manifest.json`.
- Box (immediately after): "checkit computes diff slice:
  `git diff <base>..<head> -- <repo>`".

### T6 — checkit lane (THE LOAD-BEARING STEP — make this the visual peak)
- Draw a **prominent bounded box** inside the checkit lane labeled
  **"SEALED TEMP DIR"** in red caps. Hashed/striped border. Inside the box,
  list literally:
    ```
    /tmp/checkit-XXXX/
      spec.txt                       (copied in)
      diff/                          (copied in, files only)
      phase-1-input-manifest.json    (lists exactly the above, hash-pinned)
    ```
- Below the box, list what is **NOT** copied in (red strikethrough):
  `contract.md`, `mental-model.brief.md`, `mental-model.png`,
  `~/peep-archive/<peepID>/...` (full archive path).
- Arrow into the SEALED TEMP DIR box from the bus carrying ONLY
  `spec.txt` and from the project-repo icon carrying ONLY `diff`.
- Caption underneath the box: **"hephaestus dispatched with `--dir
  <tempdir>`. The worker literally cannot open files that aren't there.
  Enforcement, not policy."**

### T7 — checkit lane, inside the SEALED TEMP DIR
- Box: "Phase 1: BLIND RECONSTRUCTION".
- Sub-arrow inside the temp dir: hephaestus run.
- Outputs leaving the temp dir to the right:
  `actual-architecture.brief.md`, `actual-architecture.png`.
- Arrow: outputs flow out of the temp dir box into the broader checkit
  lane.

### T8 — checkit lane
- Box: "checkit moves phase-1 outputs into the run folder".
- New folder icon labeled
  `~/peep-archive/<peepID>/checkit/run-<UTC-iso>-<6char-uuid>/`. Caption:
  "no counter (race-free), unique by timestamp+uuid, sortable".

### T9 — checkit lane
- Box: "Phase 2: COMPARE".
- Show this dispatch is from a *different* working directory — the
  archive folder, NOT the sealed temp dir. The worker now has access to
  EVERYTHING: contract, mental-model PNG, mental-model brief, the
  phase-1 outputs, the diff, the build-manifest.
- Output artifact: `gap-report.md`. Caption: "side-by-side compare of
  intended vs actual architecture; cites contract INVn ids and anti-claims".

### T10 — checkit lane (CONDITIONAL — drawn dashed)
- Conditional box (dashed border): "if contract.CHANGE_SURFACE includes
  any frontend file, **invoke /proofshot**".
- Sub-arrow into a small browser icon labeled `proofshot session`.
- Output: `proofshot/` folder of artifacts, dropped into the run folder.

### T11 — checkit lane
- Box: "checkit applies precedence rule and writes verdict".
- Render the precedence rule explicitly as a small flowchart inside the
  box, top to bottom:
    ```
    if build_broken     → FAILED
    elif proofshot_fail → BEHAVIORAL_FAIL
    elif contract_violation → LOGIC_GAP
    elif arch_divergence    → ARCH_GAP
    elif minor diffs        → VERIFIED
    else                    → PERFECT
    ```
- Output artifact: `verdict.md` (single token).

### T12 — checkit lane (CONDITIONAL — drawn dashed)
- Conditional box (dashed border): "if verdict ∈ {LOGIC_GAP, ARCH_GAP,
  BEHAVIORAL_FAIL, FAILED} → write `corrective-prompt.md`".
- Output: `corrective-prompt.md` artifact, dropped into the run folder.

### T13 — checkit lane
- Box: "git fetch && git commit && git pull --rebase && git push (retry
  ≤3 on conflict)".
- Drop arrow: vertical thick arrow from the run folder down to the
  orphan-branch bus, labeled **"git commit + push (orphan branch peep,
  run folder)"**.

## The orphan-branch bus (bottom strip)

Throughout the diagram, the orphan-branch bus shows a **growing
file-tree** that accumulates left to right:

- After T1: `peep-bbfa2319/{spec.txt, contract.md, mental-model.brief.md, mental-model.png}`
- After T3: `peep-bbfa2319/build-manifest.json`
- After T13: `peep-bbfa2319/checkit/run-<ts>-<uuid>/{actual-architecture.{brief.md,png}, gap-report.md, verdict.md, corrective-prompt.md?, proofshot/?}`

To the right of the bus, draw a **GitHub octocat icon** with an arrow
**from the bus to GitHub** labeled `git push origin peep` — the bus is
what talks to the remote, not the actors directly.

## Visual vocabulary

- **Cool teal** boxes: peep, checkit, analysis steps.
- **Warm orange** boxes: builder, side-effecting steps.
- **Purple** boxes: orphan-branch bus, version-control operations.
- **Neutral grey-blue** boxes: USER actions.
- **Red border + hashed background** for the SEALED TEMP DIR box. This is
  the enforcement boundary; it should pop visually.
- **Solid arrows** for required flows; **dashed arrows** for conditional
  steps (T10, T12).
- **Thick vertical arrows** drop from any producing event down to the bus.
- Monospace for filenames, peepIDs, command lines, and the precedence
  rule. Sans-serif for actor labels and event captions.

## Invariants the picture must encode

- **The SEALED TEMP DIR box must literally list both ALLOWED files and
  FORBIDDEN files.** If the picture only shows what's allowed, a viewer
  cannot see that contract.md is excluded — and that exclusion *is* the
  enforcement.
- **The build-manifest.json must appear as a first-class artifact** in the
  builder lane at T3 and as an input to checkit at T5. Hephaestus's review
  flagged its absence as the central operational hole; the diagram must
  put it on stage.
- **Phase 1 outputs must visually exit the temp dir** before they enter
  the run folder. Otherwise the picture suggests phase 1 wrote into the
  archive directly, which would defeat the seal.
- **The orphan-branch bus must show a GROWING file tree** across time, not
  a static snapshot. The eye should see things appearing as the timeline
  advances.
- **GitHub push arrow originates from the bus**, not from any actor lane.
- **The peepID `peep-bbfa2319` (or any peep-XXXXXXXX) must appear in every
  archive-path label** across the entire diagram. It is the foreign key.

## What the picture must NOT imply

- **No arrow from peep directly to builder.** Builder reads contract from
  the bus, not from peep. This was a hidden bug in the previous
  infographic and we're explicitly fixing it.
- **No write arrow from checkit into the project repo.** Checkit only
  reads from the project repo (the diff). All checkit writes go into the
  archive bus.
- **No `mental-model.png` arrow into the SEALED TEMP DIR.** Show it
  visually absent. The forbidden-files list inside the box already says so;
  no arrow may contradict it.
- **No counter-style `run-1, run-2` labels.** Use the timestamp+uuid
  literal. The previous design implied a counter, which races; the new one
  doesn't.
- **No automatic re-dispatch from corrective-prompt.md back to builder.**
  The corrective prompt is a file produced for the *next* builder session.
  Drawing an arrow back to builder would imply automation that doesn't
  exist.
- **No mtime-fallback invocation surface.** `/checkit` requires `<peepID>`
  literally; there is no "auto-detect latest" behavior in this design.
  The terminal strip at T4 should show the peepID arg explicitly.
- **No two spines.** The previous infographic had a "central peepID
  arrow" AND a "left archive bar" — one design, two visual representations.
  This time the orphan-branch bus is the SINGLE persistence object;
  peepID lives on the bus and in archive-path labels, never as a separate
  central spine.

## Tone

Clean, technical, no decoration. This is a sequence diagram, not a hero
shot. Light pastel fills with strong borders. The SEALED TEMP DIR box
gets the only "loud" visual treatment because it's load-bearing.

Aspect ratio: 1600×1000 (landscape). No watermark, no logos, no
3D effects.
