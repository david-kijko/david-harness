# checkit run-0 design review — adversarial gap analysis

Inputs reviewed:
- `contract.md`
- `mental-model.brief.md`
- `mental-model.png` (visually inspected at 1536x1024)
- `spec.txt` for the byte-level source behind the contract's SPEC paraphrase

## A. CONTRACT INTEGRITY

### A1. Does R1-R10 actually decompose the user's verbatim SPEC?

- [BLOCKER] R1 silently drops the user's phrase "peepID in the peep logs". The verbatim spec says the peep contract is "numbered with a peepID in the peep logs with version control and a backup folder" (`spec.txt:1-4`), but R1 only creates `~/peep-archive/<peepID>/` files and pushes a branch (`contract.md:40-43`). There is no log file, no log schema, no statement that the archive itself is the log, and no test obligation for logs. If "peep logs" means anything other than the archive folder, this decomposition is incomplete.

- [MAJOR] R1 adds `mental-model.brief.md` and `mental-model.png` as mandatory archive outputs (`contract.md:40-43`) even though the top-level SPEC only names a peep contract and backup folder (`spec.txt:1-6`). The embedded sub-spec does name a "PEEP architecture PNG" as source of truth (`spec.txt:21-24`), so archiving the PNG is defensible, but requiring the brief file is an author-added implementation detail. That should be stated as an assumption, not smuggled into R1 as if it were verbatim.

- [MAJOR] R2 adds discovery phrases and `/checkit` routing that the user did not specify (`contract.md:44-47`). The SPEC says the skill is at `~/.claude/skills/checkit/SKILL.md` (`spec.txt:11-14`); it does not say the skill must match `/checkit`, "verify the build", or "audit the diff". This may be useful, but it is a new product requirement.

- [BLOCKER] R3 says checkit reads `mental-model.brief.md` and `mental-model.png` before also reading the actual code diff (`contract.md:48-50`). That directly conflicts with the blind-first workflow unless R3 is explicitly phase-scoped. The sub-spec says blind reconstruction reads the diff and generates actual architecture "WITHOUT looking at the PEEP PNG" (`spec.txt:23-24`); the mental-model brief is also architecture truth and should be forbidden in phase 1.

- [BLOCKER] R4 weakens "from the diff alone" into "diff + contract + spec" (`contract.md:51-55`). The brief itself says checkit produces its own architecture image "from the diff alone" before looking at the contract architecture image (`mental-model.brief.md:17-20`). Feeding the entire contract into phase 1 is not blind if the contract contains architecture-level invariants, filenames, anti-claims, or mental-model paths.

- [MAJOR] R6 expands "proofshot for UI features" (`spec.txt:26`) into proofshot when any frontend file exists OR when the gap-report flags behavioral ambiguity (`contract.md:59-61`). The second trigger is an author-added policy. It may be a good policy, but it is not decomposed from the user's verbatim SPEC.

- [MAJOR] R8 expands corrective-prompt generation from FAILED-only in the verbatim sub-spec (`spec.txt:28-30`) to all of `{LOGIC_GAP, BEHAVIORAL_FAIL, FAILED}` (`contract.md:64-66`). The prose summary above the requirements also says "failing verdicts" (`contract.md:31-36`), but that is already the author's paraphrase, not the byte-exact SPEC. This needs an explicit decision: either only FAILED requires the file, or every non-acceptable verdict does.

- [MAJOR] R10 invents `/checkit [<peepID>]` and mtime fallback (`contract.md:68-69`). The SPEC never defines invocation syntax. Worse, mtime fallback is operationally dangerous because a pushed/pulled archive can change mtimes independently of semantic recency.

- [MAJOR] The decomposition omits a requirement for cross-referencing everything against the PEEP contract. The embedded sub-spec step 4 is explicit (`spec.txt:27`), but no Rn says "contract cross-reference" as a first-class phase. R5 only cites invariants/anti-claims from the mental-model brief (`contract.md:56-58`), and R7 only emits a token verdict (`contract.md:62-63`).

### A2. Is INV2 enforceable as written?

- [BLOCKER] INV2 is not enforceable as written because the phase-1 input set includes `contract.md`, and `contract.md` itself names `mental-model.brief.md` and `mental-model.png` as checkit inputs (`contract.md:48-50`), describes the blind firewall (`contract.md:105-111`), and gives the archive path (`contract.md:241-243`). A fresh hephaestus dispatch is not a security boundary if the prompt contains a path to forbidden files and the worker has filesystem access.

- [BLOCKER] The counterexample section admits the leak channel and then pretends a sentence of instruction fixes it: "Hephaestus has no way to see them unless the brief mentions their paths" (`contract.md:215-218`), immediately followed by the exact mitigation "forbids reading anything in the peep-archive folder other than spec.txt and contract.md" (`contract.md:219-223`). That is policy, not enforcement. A worker can still open the files; an adversarial or merely confused worker can leak the mental model.

- [MAJOR] The contract never requires capturing the actual phase-1 prompt, allowed file list, cwd, command line, or transcript. Without a prompt/transcript artifact, phase 2 cannot prove what phase 1 saw. Blind reconstruction needs an audit artifact like `phase-1-input-manifest.json` and the literal hephaestus command, not just a claim.

- [MAJOR] There is an architectural contradiction between `mental-model.brief.md` and `contract.md`: the brief says phase 1 draws architecture "from the diff alone" (`mental-model.brief.md:17-20`), while R4 allows `diff + contract + spec` (`contract.md:51-55`). If the contract is allowed, then the blind output can be contaminated by requirements prose and intended architecture even without opening the PNG.

### A3. Are the NTn obligations runnable and probative?

- [BLOCKER] NT2 is a fake proof. `comm -12 <(sort mental-model.brief.md) <(sort actual-architecture.brief.md) | wc -l` (`contract.md:187-191`) compares sorted whole lines, not "strings", not concepts, not prompt context, and not image leakage. It can miss copied paragraphs with whitespace changes and can flag boilerplate lines. It proves neither blind reconstruction nor absence of PEEP PNG access.

- [MAJOR] NT2 is not even aligned with the claimed input ban. It checks overlap with `mental-model.brief.md`, but the critical forbidden object in the user sub-spec is the PEEP architecture PNG (`spec.txt:21-24`). The test says nothing about whether phase 1 viewed `mental-model.png`.

- [MAJOR] NT1's archive test checks files and log head (`contract.md:181-185`) but not that the commit was pushed to the orphan branch or that the path is inside the david-harness remote requested by the user. R1 includes push; NT1 does not test push.

- [MAJOR] NT4 does not enforce "exactly one" verdict. `grep -E "^(PERFECT|...|FAILED)$" verdict.md` (`contract.md:197-198`) passes if the file contains multiple verdict lines plus arbitrary junk. The requirement says `verdict.md` contains exactly one of the six (`contract.md:62-63`).

- [MAJOR] NT5 has no concrete pre/post command and is race-prone. "log advances by 1 per run" (`contract.md:200`) is not meaningful without capturing the previous HEAD before the run. `git ls-remote origin peep | head -1` can match local HEAD while still missing the intended run contents if the wrong commit was pushed.

- [MAJOR] NT6 is underspecified and barely runnable. It says `/checkit` targets the most recent mtime with two folders present (`contract.md:202-203`) but gives no command, no fixture creation, no expected output, and no way to observe the selected peepID besides reading whatever files happen to be emitted.

### A4. Is the verdict ladder orthogonal?

- [BLOCKER] The ladder is not orthogonal because no decision rules define precedence among ARCH_GAP, LOGIC_GAP, and BEHAVIORAL_FAIL. An architecture gap can be a business-logic gap; a behavioral failure can expose a logic gap; and an implementation that fails proofshot may also diverge architecturally. The contract only enumerates tokens (`contract.md:62-63`) and calls the ladder "sound by exhaustion" (`contract.md:225`), which is not a classification rule.

- [MAJOR] PERFECT and VERIFIED overlap. The contract does not define whether PERFECT means visual + behavioral + contract exactness, while VERIFIED allows harmless implementation differences. Without acceptance criteria, two reviewers can assign different top verdicts to the same run.

- [MAJOR] FAILED is ambiguous. In the verbatim sub-spec, FAILED is the only rung explicitly tied to `corrective-prompt.md` (`spec.txt:28-30`); in the contract, corrective-prompt is emitted for three rungs (`contract.md:64-66`). That makes FAILED both a verdict and a remediation trigger, while LOGIC_GAP and BEHAVIORAL_FAIL are also remediation triggers.

### A5. What is still missing despite "READY TO IMPLEMENT"?

- [BLOCKER] The plan never defines how checkit identifies "the actual code diff". R3 says it reads the actual code diff from the project repo (`contract.md:48-50`), but there is no `--repo`, `--base`, `--head`, current-working-directory rule, PR number, commit range, staged/untracked policy, or peepID-to-commit mapping. Implementation will immediately stall or audit the wrong slice.

- [BLOCKER] There is no concurrency model for `run-N/`. R3/R9 imply multiple run folders and immediate commit/push (`contract.md:22-23`, `contract.md:67`), but there is no lock, atomic directory creation, pull/rebase protocol, or conflict resolution for two agents creating `run-1/` in parallel.

- [MAJOR] The orphan branch bootstrap is hand-waved. IP4 says the worktree is "already created this turn" (`contract.md:91`), and R1/R9 require push (`contract.md:40-43`, `contract.md:67`), but the contract does not specify how a fresh machine creates, tracks, fetches, or repairs the orphan `peep` branch.

- [MAJOR] The actual skill install path is muddled. The user's context says the harness pattern is `~/david-harness/claude/skills/<name>/` symlinked to `~/.claude/skills/<name>/`; R2 only names `~/.claude/skills/checkit/SKILL.md` (`contract.md:44-47`), while IP5/IP6 add harness source and symlink (`contract.md:92-95`). The source of truth should be a requirement, not just an integration point.

- [MAJOR] The proofshot obligation is not implementable as written. R6 says invoke `/proofshot` for UI features (`contract.md:59-61`), and INV6 names a lifecycle (`contract.md:128-132`), but no contract field says how to launch the app, what URL to test, which flows to exercise, or how to map contract NEW TEST OBLIGATIONS to browser actions.

- [MAJOR] The contract never specifies artifact schemas. `actual-architecture.brief.md`, `gap-report.md`, `verdict.md`, and `corrective-prompt.md` are named, but their required headings, evidence format, cited inputs, and machine-checkable fields are not defined beyond thin grep checks (`contract.md:187-200`).

## B. BRIEF vs IMAGE CONCORDANCE

### B1. Does the rendered image encode every required invariant?

- [FINE] The firewall is drawn as a real visual barrier. In the image bottom center, the red brick vertical wall labeled "BLIND RECONSTRUCTION FIREWALL" clearly divides PHASE 1 and PHASE 2.

- [FINE] `mental-model.png` is visually sealed in phase 1. In the image lower-left of the checkit band, the greyed image icon is labeled "mental-model.png sealed until phase 2" with a dashed blocked path and red X before the wall.

- [FINE] The peepID appears at the computation point, archive bar, and checkit ingress. It is shown under the peep box with `sha256(SPEC)[0:8]`, vertically inside the left archive bar, and on the central downward arrow entering checkit.

- [FINE] The archive bar shows both peep artifacts and checkit artifacts in the same folder. The image left bar lists `spec.txt`, `contract.md`, `mental-model.brief.md`, `mental-model.png`, and `checkit/run-1/...` outputs.

- [MINOR] The GitHub push arrow mostly satisfies the brief but is visually weak. The upper-left "automatic push" arrow is inside the archive panel near the GitHub label, so it does not originate from peep or checkit directly. However, the arrow direction and octocat/GitHub relationship are visually odd: it reads like octocat pushes down to GitHub, not like the archive worktree pushes to remote.

- [MAJOR] The peepID/archive spine invariant is only half-encoded. The brief says the archive bar is "the spine that holds everything together" (`mental-model.brief.md:160`) and B5 asks whether the peepID spine connects the three bands and archive bar. The rendered image has two separate spines: a left archive bar and a central vertical peepID arrow. They share text, but they are not one continuous visual object.

- [MINOR] The verdict ladder shows all six rungs in order with green-to-red progression, but the `BEHAVIORAL_FAIL` text is too small/truncated in the rendered strip. The semantic rung exists, yet the label is not robustly readable at normal view.

### B2. Does the image violate any "MUST NOT imply" item?

- [FINE] No direct peep skill -> builder agent arrow is drawn. The orange dashed contract line in the BUILD band starts from the archive side and points to the builder, matching "builder reads the contract" rather than tight peep coupling.

- [FINE] No checkit write arrow into the project repo appears. The project repo only feeds builder's diff into checkit; checkit outputs point to audit artifacts and the archive.

- [FINE] No checkit phase-1 access to `mental-model.png` is implied. The grey dashed line is visibly blocked by a red X before the firewall.

- [FINE] No `~/.codex/skills/checkit/` mirror, counter file, central registry, NotebookLM, MCP server, DB, or message queue is drawn.

- [FINE] No automatic builder-trigger from failed verdict is drawn. `corrective-prompt.md` is an output file on the right, not an arrow back to the builder.

### B3. Is the blind reconstruction firewall visually real and phase 1 sealed?

- [FINE] Yes, the firewall is the strongest element in the audit band: red brick wall, red glow, all-caps label, and a one-way phase-1-outputs arrow through it. This does communicate that phase 1 output crosses to phase 2, not that phase 2 data crosses backward.

- [MAJOR] The image does not show the full enforcement mechanism, only the policy. It visually blocks `mental-model.png`, but it does not show the actual allowed phase-1 input manifest: contract? spec? diff only? The image says phase 1 receives contract.md and builder's diff, which inherits the contract's contamination problem from A2/A5.

### B4. Does the verdict ladder show all six rungs in correct order/color?

- [FINE] The order is correct: PERFECT, VERIFIED, ARCH_GAP, LOGIC_GAP, BEHAVIORAL_FAIL, FAILED, left to right.

- [FINE] The color progression is correct: green, green-yellow, yellow, orange/yellow-orange, red-orange, red.

- [MINOR] The ladder is too small for a load-bearing decision mechanism. The `ARCH_GAP` highlight is visible, but the later labels are cramped enough that the diagram is not self-documenting without the brief.

### B5. Does the peepID spine visually connect the three bands and archive bar?

- [MAJOR] No. The central peepID arrow connects PLAN -> BUILD -> AUDIT, while the left archive bar has its own separate vertical peepID label. The two are connected only by horizontal archive arrows and repeated text. That makes the archive look like a sidecar storage panel, not the single foreign-key spine promised by the brief (`mental-model.brief.md:21-28`, `mental-model.brief.md:130-160`).

## C. HIDDEN ASSUMPTIONS THE AUTHOR DIDN'T STATE

### C1. BUILDER workflow assumptions that may not hold

- [BLOCKER] The design assumes the builder's diff is discoverable from "the project repo" (`contract.md:48-50`) and visually from a single folder icon. That fails for worktrees, PR branches, multiple commits, generated files, staged-vs-unstaged changes, untracked files, submodules, and multi-repo features. Checkit needs an explicit diff source contract.

- [MAJOR] The design assumes the builder implemented against the archived contract. The diagram shows a dashed contract line into builder, but no mechanism records which peepID the builder used, which commit started the build, or whether the builder mixed requirements from another session.

### C2. How does checkit know which commit/diff to audit?

- [BLOCKER] It doesn't. There is no peepID -> commit-range mapping anywhere in `contract.md`. The user asked for auditing what the builder actually shipped; the design names "actual code diff" (`contract.md:48-50`) but never defines the slice. This is the central missing business object.

- [MAJOR] `/checkit [<peepID>]` is insufficient invocation surface (`contract.md:68-69`). A peepID identifies the contract, not the code changes. Minimum viable invocation needs something like `/checkit <peepID> --repo <path> --base <sha> --head <sha>` or a recorded build manifest produced by the builder.

### C3. sha8 collision failure mode

- [MAJOR] `sha8` gives only 32 bits of namespace (`contract.md:19-21`, `contract.md:121-126`). That is probably fine for a toy archive, but it is weak for a permanent audit log. A collision means two different SPECs map to the same folder, so peep artifacts overwrite each other and checkit runs become attached to the wrong source of truth.

- [MAJOR] The contract has no collision detection. It should at least compare existing `spec.txt` to the new verbatim SPEC before writing, and on mismatch either extend the hash or create a collision suffix. Determinism is not enough.

### C4. Re-running peep on the same SPEC

- [MAJOR] INV5 explicitly says overwriting `contract.md`, `mental-model.brief.md`, and `mental-model.png` is acceptable because they are derived from SPEC (`contract.md:121-126`). That ignores non-determinism in peep, image generation, template versions, and model behavior. Same SPEC can produce a different contract or mental model later; overwriting mutates the source of truth for prior checkit runs.

- [MAJOR] If re-run is intended to be idempotent, the archive needs content-addressed or versioned plan artifacts, e.g. `plan-run-N/` or commit-pinned references in each checkit run. Relying on git history alone makes the current folder lie about which contract a past run audited.

### C5. Orphan branch merge conflict / parallel agents

- [BLOCKER] Two agents archiving in parallel will race on both `run-N/` naming and branch HEAD. One push will be rejected or, worse, both will create `run-1/` for the same peepID locally. The contract has no lock file, atomic mkdir strategy, fetch-before-numbering rule, rebase strategy, or conflict retry loop.

- [MAJOR] The orphan branch is both storage and coordination mechanism. Git can store the audit trail, but it is not a queue or lock manager. The design needs a simple concurrency rule before implementation, even if it is just "fetch, allocate run dir by timestamp+short random suffix, commit, pull --rebase, retry push."

## D. SCOPE & SIMPLICITY

### D1. Is this over-engineered? What can be cut?

- [MAJOR] Yes, parts are over-engineered relative to the core capability. The core is: given peep contract + builder diff, produce blind actual-architecture summary, compare to intended architecture, run behavior checks when applicable, emit verdict and corrective prompt. The permanent archive, image generation, proofshot, six-rung ladder, and orphan branch are all useful, but not all need to be v1 blockers.

- [MAJOR] Cut or defer the generated `actual-architecture.png` for v1. A structured `actual-architecture.brief.md` plus contract/diff citations is easier to verify than an image and avoids delegating image rendering just to prove a blind reconstruction. Add the image once the textual blind phase is trustworthy.

- [MINOR] Cut the mtime fallback. `/checkit` without a peepID is convenient but unsafe; it adds ambiguity with little core value. Force explicit peepID until the archive has a reliable manifest/index.

- [MINOR] Collapse PERFECT/VERIFIED for v1 unless the contract defines objective differences. A five-rung or four-rung ladder with tie-breakers would be easier to implement correctly.

### D2. Is mission-critical functionality missing?

- [BLOCKER] Yes: the user-facing invocation for a project outside `~/peep-archive` is missing. The skill lives in Claude, but the archive lives elsewhere, and the project repo can be anywhere. The design does not say whether the user runs `/checkit` from the project cwd, passes a repo path, passes a branch, or points to a PR.

- [BLOCKER] The build manifest is missing. Checkit needs to know: peepID, repo path, base commit, head commit or patch file, untracked inclusion policy, test commands, app launch command for proofshot, and any deployment URL. Without that, the audit cannot be reproduced.

- [MAJOR] The contract does not specify read-only enforcement for the project repo. The brief says checkit must not edit the repo (`mental-model.brief.md:210-212`), but the contract never turns that into an invariant or NT. A verifier skill with hephaestus access could accidentally write files during analysis.

## E. BUSINESS LOGIC THE IMAGE SURFACED THAT PROSE HID

### E1. Relationships/data flows visually obvious in the image but not explicit in prose

- [MAJOR] The image exposes that there are two distinct identity mechanisms: the central peepID arrow and the left archive folder label. The prose calls peepID the foreign key (`mental-model.brief.md:21-24`), but does not explicitly resolve whether the archive folder or central spine is authoritative. This matters for implementation because path identity and diff identity are different things.

- [MAJOR] The image makes the missing diff provenance obvious. The builder emits "git diff = the slice checkit will audit" into a generic project repo icon, then checkit consumes "builder's diff". There is no visual object representing base/head commits, patch file, PR, or build manifest. That absence is the design's biggest operational hole.

- [MAJOR] The image shows `contract.md` entering phase 1, which reveals the blind contamination risk more clearly than the prose. If contract.md includes intended architecture prose, then phase 1 is not purely reconstructed from shipped code.

- [MINOR] The image shows checkit artifacts going right and archive arrows going left, which implies a two-step write: produce files locally, then archive/push. The contract says commits/pushes happen immediately (`contract.md:67`) but does not define whether artifacts are first generated in project cwd, temp, or directly under archive.

### E2. What does the brief promise that the image does not deliver?

- [MAJOR] The brief promises the archive is the spine that holds everything together (`mental-model.brief.md:130-160`), but the image makes the archive a left-side panel plus a separate central peepID spine. This weakens the central mental model: the archive is not visibly the single joining object.

- [MAJOR] The brief promises phase 2 receives both architectures side by side, with peep PNG now allowed in (`mental-model.brief.md:111-115`). The image shows both inside phase 2, but it does not show a clear allowed arrow from the sealed `mental-model.png`/archive into phase 2 after the firewall. The viewer sees a blocked line to the wall, then the peep PNG magically appears inside phase 2.

- [MINOR] The brief promises the builder band is intentionally less detailed and faded (`mental-model.brief.md:65-83`). The rendered builder is clear, bright orange, and visually prominent. It is not catastrophic, but it slightly overweights the builder relative to the audit mechanism.

- [MINOR] The brief asks for arrows from top artifacts to archive and bottom artifacts to archive (`mental-model.brief.md:154-158`). The image has archive arrows, but the top arrow is visually detached from the concrete `contract.md` and `mental-model.png` icons. It reads as peep-box-to-archive more than artifact-to-archive.

## Severity totals

- BLOCKER: 14
- MAJOR: 37
- MINOR: 8
- FINE: 12
