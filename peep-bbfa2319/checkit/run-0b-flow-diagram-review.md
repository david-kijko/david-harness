# checkit run-0b flow diagram review — adversarial gap analysis

Inputs reviewed in order: `spec.txt`, `checkit/run-0-design-review.md`, `flow-diagram.brief.md`, and the rendered `flow-diagram.png` at 1536x1024. Additional enforcement check: `$ hephaestus --help` and `/home/david/.hephaestus/run.sh` were inspected because the brief's central claim depends on what `--dir` actually enforces.

## A. BLOCKER REGRESSION CHECK

1. [MAJOR] [MITIGATED] Prior blocker: missing meaning of "peep logs" (`checkit/run-0-design-review.md:13`). The new brief makes the orphan branch bus the persistent log every lane writes to (`flow-diagram.brief.md:5-8`) and the image bottom bus shows accumulated `peep-bbfa2319/` contents. This partially resolves the ambiguity, but it still never says "the archive branch is the peep log" nor defines a log schema, so contract v2 must make that equivalence explicit.

2. [MAJOR] [MITIGATED] Prior blocker: checkit read `mental-model.brief.md`/PNG too early (`checkit/run-0-design-review.md:19`). The brief now phase-scopes access: T6 excludes `contract.md`, `mental-model.brief.md`, and `mental-model.png` from phase 1 (`flow-diagram.brief.md:97-114`), while T9 permits everything for comparison (`flow-diagram.brief.md:130-137`). Residual: the rendered image draws the T7 "Phase 1: BLIND RECONSTRUCTION" box to the right of, not inside, the red SEALED TEMP DIR, so the pixels undermine the claimed phase boundary.

3. [FINE] [FIXED] Prior blocker: blind reconstruction was weakened from diff-alone to diff+contract+spec (`checkit/run-0-design-review.md:21`). The new T6 allowed set is only `spec.txt`, `diff/`, and `phase-1-input-manifest.json` (`flow-diagram.brief.md:100-111`), and the image's sealed box lists exactly those as ALLOWED. That fixes the contract-contamination part of the old blocker; enforcement is separately addressed below.

4. [BLOCKER] [NEW-BLOCKER] Prior blocker: INV2 was not enforceable because the phase-1 prompt/path still leaked forbidden files (`checkit/run-0-design-review.md:33`). The flow improves the copied input set, but it introduces a stronger false claim: T6 says the worker "literally cannot open files that aren't there" (`flow-diagram.brief.md:112-114`). On this machine, `hephaestus --dir <tempdir>` maps to `codex exec -C <workdir>` with `features.use_linux_sandbox_bwrap=false` and `--dangerously-bypass-approvals-and-sandbox` (`/home/david/.hephaestus/run.sh:78-85`), so the worker can still read `/home/david/peep-archive/...` if instructed or confused.

5. [BLOCKER] [NEW-BLOCKER] Prior blocker: the design called policy "enforcement" (`checkit/run-0-design-review.md:35`). The new diagram doubles down visually: the red box caption in the image says "Enforcement, not policy," and the brief calls the SEALED TEMP DIR "the enforcement mechanism" (`flow-diagram.brief.md:15-17`). That is a regression in epistemic honesty: the only real controls are prompt wording, copied-input minimization, and possible transcript audit, not filesystem denial.

6. [MAJOR] [MITIGATED] Prior blocker: NT2 was a fake blind-proof overlap test (`checkit/run-0-design-review.md:43`). The new brief adds `phase-1-input-manifest.json` that lists the copied files and hashes (`flow-diagram.brief.md:100-106`), which is a better audit primitive. It is still insufficient without recording the exact hephaestus command, prompt, cwd, sandbox mode, and transcript; the manifest proves what checkit copied, not what the worker could access.

7. [FINE] [FIXED] Prior blocker: verdict ladder lacked precedence (`checkit/run-0-design-review.md:57`). T11 now renders an explicit precedence rule from `build_broken` through `minor diffs`/`PERFECT` (`flow-diagram.brief.md:145-157`), and the image contains that rule inside the verdict box. Contract v2 still needs exact definitions for `minor diffs`, but the old "no precedence" blocker is resolved.

8. [MAJOR] [MITIGATED] Prior blocker: no way to identify the actual code diff (`checkit/run-0-design-review.md:65`). T3 creates `build-manifest.json` with `repo`, `base`, `head`, `untracked_policy`, `tests`, and `app` fields (`flow-diagram.brief.md:77-83`), and T5 has checkit compute `git diff <base>..<head>` (`flow-diagram.brief.md:90-96`). Residual blocker moved: there is no commit-lineage validation that `base..head` is the builder's intended slice rather than unrelated commits.

9. [FINE] [FIXED] Prior blocker: `run-N/` had no concurrency model (`checkit/run-0-design-review.md:67`). T8 uses `run-<UTC-iso>-<6char-uuid>/` with no counter (`flow-diagram.brief.md:124-128`), and T13 adds fetch/commit/pull-rebase/push retry (`flow-diagram.brief.md:164-169`). That removes the counter race.

10. [MAJOR] [MITIGATED] Prior blocker: builder diff discoverability assumed a generic project repo (`checkit/run-0-design-review.md:129`). The build manifest is now the missing business object, and it is visible in both the builder lane and the bus. Remaining gap: manifest contents are trusted without validating repo cleanliness, ancestry, submodules, generated-file policy, or whether the builder actually consumed the referenced peepID.

11. [MAJOR] [MITIGATED] Prior blocker: no peepID-to-commit mapping (`checkit/run-0-design-review.md:135`). The manifest includes `{peepID, repo, base, head, ...}` (`flow-diagram.brief.md:77-80`), so the mapping exists as an artifact. It is still not guarded: the flow does not show a graceful failure for missing/wrong-peepID manifest, nor a check that `head` descends from `base` and is not a multi-builder range.

12. [FINE] [FIXED] Prior blocker: parallel agents racing on `run-N/` and branch HEAD (`checkit/run-0-design-review.md:153`). Timestamp+uuid run folders plus T13 rebase/retry are a credible minimal concurrency story (`flow-diagram.brief.md:126-128`, `flow-diagram.brief.md:164-169`). A future contract may still need exact retry failure behavior, but the original race is no longer a blocker.

13. [MAJOR] [MITIGATED] Prior blocker: user-facing invocation for projects outside `~/peep-archive` was missing (`checkit/run-0-design-review.md:171`). The flow makes `/checkit <peepID>` read repo/base/head from the archived manifest, so the user no longer has to pass repo flags at checkit time. Hidden coupling remains: if the builder did not write the manifest, wrote it under a different peepID, or auto-polls without a user handoff, the flow does not define recovery.

14. [FINE] [FIXED] Prior blocker: build manifest was missing (`checkit/run-0-design-review.md:173`). The brief explicitly calls it "the new artifact" and lists the necessary operational fields (`flow-diagram.brief.md:77-83`); the image shows it as a builder-lane artifact, a bus entry, and a T5 checkit input. This is the clearest real improvement over run-0.

## B. FLOW DIAGRAM INTEGRITY

### B1. Does the picture accurately render every event T0-T13 from the brief?

- [FINE] T0 is present: image top-left USER box says the user writes `plan.md` and invokes peep, with a diagonal arrow into the peep lane, matching `flow-diagram.brief.md:45-48`.
- [MINOR] T1 is mostly present but cramped: the image shows certificate fill, `sha8(SPEC)`, archive write, and `/imagegen -> hephaestus -> Codex image_gen`, matching `flow-diagram.brief.md:50-61`. The `mental-model.brief.md` filename is line-broken and the formula is tiny, but the event is recoverable.
- [MAJOR] T2 is misplaced: the brief says the `contract.md` arrow should originate from the bus and go up into the builder's T2 box (`flow-diagram.brief.md:63-68`). The image instead shows a vertical bus-to-USER arrow into the "USER hands the contract" box and no clear diagonal handoff into the builder lane. That preserves the human action but obscures the critical bus-to-builder consumption path.
- [FINE] T3 is present: the builder modifies a project repo, commits in that repo, writes `build-manifest.json`, and drops it to the bus, matching `flow-diagram.brief.md:70-83`.
- [MAJOR] T4 arrow is visually wrong: the image has `/checkit peep-bbfa2319`, but the long diagonal arrow lands near the T7 Phase 1 box, visually skipping T5 manifest-read and T6 sealing. The brief says T4 should enter the checkit lane before T5 (`flow-diagram.brief.md:85-96`).
- [FINE] T5 is present: image left of the sealed box shows "checkit reads build-manifest.json from the bus" and "checkit computes diff slice," with bus arrows for manifest/spec and project diff, matching `flow-diagram.brief.md:90-96`.
- [FINE] T6 is present and visually loud: red hashed SEALED TEMP DIR box lists allowed and forbidden files, matching `flow-diagram.brief.md:97-114`.
- [BLOCKER] T7 is rendered outside the seal: the brief requires T7 "inside the SEALED TEMP DIR" and outputs leaving the tempdir (`flow-diagram.brief.md:116-122`). In the image, the "Phase 1: BLIND RECONSTRUCTION -> hephaestus run" box sits to the right of the red sealed-temp-dir boundary, with outputs further right. The pixels imply phase 1 runs after leaving the sealed area, which breaks the diagram's central claim.
- [FINE] T8 is present: image shows checkit moving phase-1 outputs into a `run-<UTC-iso>-<6char-uuid>/` folder and bottom bus shows a concrete timestamp+uuid run folder, matching `flow-diagram.brief.md:124-128`.
- [BLOCKER] T9 is missing as a first-class phase: the brief requires a distinct "Phase 2: COMPARE" box from the archive folder with access to contract, mental model, phase-1 outputs, diff, and manifest (`flow-diagram.brief.md:130-137`). The image has a small caption under the verdict area saying "side-by-side compare; cites contract INV ids and anti-claims," but no T9 box, no separate working-directory indication, and no explicit allowed inflow from the archive into phase 2.
- [FINE] T10 is present and conditional: dashed proofshot box and browser/session/folder outputs match `flow-diagram.brief.md:139-143`.
- [FINE] T11 is present: precedence rule and `verdict.md` artifact match `flow-diagram.brief.md:145-157`.
- [FINE] T12 is present and conditional: dashed corrective-prompt box and artifact match `flow-diagram.brief.md:159-162`.
- [FINE] T13 is present: git fetch/commit/pull-rebase/push retry box and vertical drop to bus match `flow-diagram.brief.md:164-169`.

### B2. Is the SEALED TEMP DIR box visually load-bearing and does it list both allowed and forbidden files?

- [MAJOR] The box is visually load-bearing in style but not in topology. It is red, hashed, central, and lists ALLOWED plus FORBIDDEN files, satisfying `flow-diagram.brief.md:198-203`. However, because T7 is outside the box, the visual load-bearing element becomes a staging manifest box rather than the execution boundary the brief requires.
- [FINE] It lists both categories: image center-left T6 box includes ALLOWED `/tmp/checkit-XXXX/`, `spec.txt`, `diff/`, `phase-1-input-manifest.json`, and FORBIDDEN `contract.md`, `mental-model.brief.md`, `mental-model.png`, and `/peep-archive/peep-bbfa2319/...`.

### B3. Does the orphan-branch bus show file-tree growth across time?

- [FINE] Yes. The image bottom bus shows a left snapshot after T1, a larger snapshot after T3 including `build-manifest.json`, and a later run-folder snapshot after T13. This matches the growing file tree required by `flow-diagram.brief.md:171-179`.

### B4. Is `build-manifest.json` first-class in builder lane and consumed by checkit at T5?

- [FINE] Yes. The image has an orange builder-lane `build-manifest.json` box with schema fields, a bus entry containing `build-manifest.json`, and a checkit T5 box reading it from the bus. This satisfies `flow-diagram.brief.md:204-207`.

### B5. Is the run folder labeled `run-<UTC-iso>-<6char-uuid>` with no counter?

- [FINE] Yes. The checkit-lane run folder uses the literal pattern, and the bottom bus uses a concrete timestamp+uuid example. There is no `run-1`/`run-2` counter, satisfying `flow-diagram.brief.md:126-128` and `flow-diagram.brief.md:229-231`.

### B6. Are T10 and T12 conditional/dashed?

- [FINE] Yes. Both the proofshot and corrective-prompt boxes have dashed borders in the image, matching `flow-diagram.brief.md:139-143` and `flow-diagram.brief.md:159-162`.

### B7. Is the GitHub push arrow originating from the bus?

- [FINE] Yes. The image bottom-right arrow labeled `git push origin peep` starts from the purple bus/run-folder area and points to GitHub, matching `flow-diagram.brief.md:180-182`.

### B8. Does any visual element contradict the brief's "MUST NOT imply" list?

- [FINE] No direct peep-to-builder arrow is drawn; the builder does not consume directly from peep, matching `flow-diagram.brief.md:220-222`.
- [FINE] No checkit write arrow into the project repo is drawn; the repo only feeds `diff/` toward the sealed area, matching `flow-diagram.brief.md:223-225`.
- [FINE] No `mental-model.png` arrow enters the sealed temp dir; it appears only in the forbidden list, matching `flow-diagram.brief.md:226-228`.
- [FINE] No counter-style run labels or mtime fallback invocation appear; the T4 strip says `/checkit peep-bbfa2319`, matching `flow-diagram.brief.md:229-238`.
- [FINE] No automatic arrow from `corrective-prompt.md` back to the builder is drawn, matching `flow-diagram.brief.md:232-235`.
- [MAJOR] The T4 arrow landing at T7 contradicts the intended sequence even if not one of the explicit MUST-NOT bullets: it visually implies `/checkit` initiates phase 1 directly rather than first reading `build-manifest.json` and constructing the sealed temp dir.

## C. ENFORCEMENT vs POLICY

### C1. Is "absence, not policy" genuinely enforced on this machine?

- [BLOCKER] No. The copied tempdir contents are absent from the worker's current directory, but the worker process is not jailed. The hephaestus wrapper defaults to `sandbox="dangerous"` (`/home/david/.hephaestus/run.sh:4-7`), disables bwrap (`/home/david/.hephaestus/run.sh:83`), bypasses approvals and sandboxing (`/home/david/.hephaestus/run.sh:84`), and uses `-C "$workdir"` only to select the Codex working directory (`/home/david/.hephaestus/run.sh:85`). Therefore an agent can still `cd /home/david/peep-archive/peep-bbfa2319` or open forbidden files by absolute path. What actually holds: the prompt can omit forbidden files, the cwd can be a tempdir, the manifest can hash copied inputs, and later audit can inspect transcripts. What does not hold: kernel-level filesystem denial.

### C2. Does `--dir <tempdir>` constrain reads or just set CWD/project dir?

- [BLOCKER] It just sets the working/project directory. The wrapper parses `--dir` by assigning `workdir="$2"` (`/home/david/.hephaestus/run.sh:33-35`) and later passes that as `codex exec -C "$workdir"` (`/home/david/.hephaestus/run.sh:78-86`). There is no chroot, mount namespace, user namespace, denylist, or bind-mount boundary in this code path. The brief's caption at `flow-diagram.brief.md:112-114` is therefore false as a statement about this host.

### C3. Minimum technical fixes, ranked by effort

- [MAJOR] Lowest effort, not enforcement: accept policy and add transcript/prompt audit. Keep the tempdir, write `phase-1-input-manifest.json`, capture hephaestus command, cwd, sandbox mode, prompt, stdout/stderr/transcript, and run a post-hoc scan for forbidden-path access. This is useful but must be labeled "audit," not "sealed."
- [MAJOR] Low-to-medium effort actual enforcement: run the phase-1 worker as a different Unix user with ACLs/permissions denying `/home/david/peep-archive` and binding only the tempdir/project diff readable. This can be lighter than containers but needs careful ownership and no shared readable home secrets.
- [MAJOR] Medium effort actual enforcement: `bwrap`/Bubblewrap mount namespace. Bind the tempdir as `/work`, optionally bind a read-only sanitized diff directory, provide an empty HOME, hide `/home/david/peep-archive`, and enable Codex's Linux sandbox instead of forcing `features.use_linux_sandbox_bwrap=false`.
- [MAJOR] Medium-to-high effort actual enforcement: direct Linux user+mount namespace setup without bwrap. This is essentially rebuilding bwrap's job and is more error-prone unless there is a strong reason to avoid bwrap.
- [MAJOR] Highest operational effort but clearest isolation: rootless Docker/Podman with only the tempdir mounted, no host home mount, explicit network policy, and read-only mounts. This is heavier but easiest to explain and audit.

## D. MISSING / NEW HIDDEN ASSUMPTIONS

### D1. What if `base..head` spans multiple builders or unrelated commits?

- [BLOCKER] The flow does not validate commit lineage or ownership. T5 computes `git diff <base>..<head> -- <repo>` (`flow-diagram.brief.md:94-95`), but nothing checks that `head` descends from `base`, that the range belongs to one builder session, that the commits were made after the manifest's peepID was consumed, or that unrelated commits are excluded. Minimum contract v2 fix: validate `git merge-base --is-ancestor base head`, record builder branch/commit author/session, reject dirty/untracked ambiguity unless declared by `untracked_policy`, and include a manifest signature or at least a self-consistency check.

### D2. What if `/checkit <peepID>` has no matching manifest?

- [MAJOR] The brief removes the no-arg mtime fallback (`flow-diagram.brief.md:236-238`) but does not define graceful failure for missing `build-manifest.json`. Since T5 depends on that artifact (`flow-diagram.brief.md:90-96`), contract v2 needs an explicit error path: emit a failed run or no run? write `missing-build-manifest.md`? print a corrective instruction to run the builder manifest step? Without that, implementation will either crash or silently audit the wrong thing.

### D3. Is the human-in-the-loop builder handoff a hidden coupling?

- [MAJOR] Yes. T2 says "USER hands the contract to a builder agent" (`flow-diagram.brief.md:63-68`), and the image emphasizes the USER lane. In practice, the builder may be manually dispatched, auto-poll the bus, continue from an existing session, or be hephaestus itself. If the manifest is the real synchronization object, the design should not require a human handoff as the only path. Contract v2 should define the builder obligation: any builder, human-dispatched or automated, must read `contract.md` from the bus and write a manifest for the same peepID before checkit can run.

### D4. What about huge diffs, binaries, and generated files?

- [BLOCKER] The sealed tempdir says `diff/ (copied in, files only)` (`flow-diagram.brief.md:101-106`) but defines no diff filtering. A 10k-file diff can blow prompt/context limits; binary blobs cannot be meaningfully reconstructed as text; generated files can drown the real change; secrets may be copied into phase 1. Contract v2 needs include/exclude policy, size limits, binary handling, generated-file filtering, secret scanning, and a manifest field recording what was omitted and why.

## E. SCOPE & PRIORITY (carryover from D in run-0)

### E1. Does the flow keep over-engineered parts or cut/defer any?

- [MAJOR] It cuts one unsafe convenience: no-arg `/checkit`/mtime fallback is explicitly forbidden (`flow-diagram.brief.md:236-238`), and the counter-based run folder is replaced by timestamp+uuid. Those are real simplifications.
- [MAJOR] It keeps most of the heavy machinery in phase 1: image generation via `/imagegen` for peep (`flow-diagram.brief.md:57-59`), generated `actual-architecture.png` in phase 1 (`flow-diagram.brief.md:116-122`), proofshot (`flow-diagram.brief.md:139-143`), the six-rung ladder (`flow-diagram.brief.md:145-157`), and immediate orphan-branch pushes (`flow-diagram.brief.md:164-182`). The flow is better organized, but not notably leaner.
- [MINOR] The six-rung ladder is more implementable now because precedence is explicit, but it is still a lot for v1 unless `PERFECT` vs `VERIFIED` and `ARCH_GAP` vs `LOGIC_GAP` are objectively testable.

### E2. Is `actual-architecture.png` still required in phase 1?

- [MAJOR] Yes. T7 outputs both `actual-architecture.brief.md` and `actual-architecture.png` (`flow-diagram.brief.md:116-122`), and the image shows both artifacts. That preserves the run-0 concern: phase 1 still needs another image-generation hop before the textual blind reconstruction is trustworthy. Worse, because phase 1 is not actually jailed on this host, image generation is another prompt/tool path where forbidden context could leak unless the enforcement story is fixed first.

## VERDICT

This flow demonstrates that the author understood several run-0 operational holes, especially the missing `build-manifest.json`, counter-race, explicit peepID invocation, and verdict precedence. But they are still bullshitting themselves about the most load-bearing claim: the SEALED TEMP DIR is drawn and described as enforced isolation even though `hephaestus --dir` only sets CWD and the local wrapper explicitly bypasses sandboxing. Until that is corrected, and until T7/T9 are redrawn so phase 1 really runs inside the sealed boundary and phase 2 is a first-class compare step, this is not safe to commit into contract v2 or skill code.

## SEVERITY TOTALS

BLOCKER=8 MAJOR=21 MINOR=2 FINE=25

## NET PROGRESS vs run-0

Of the 14 prior BLOCKERS: [FIXED]=5 / [MITIGATED]=7 / [UNCHANGED]=0 / [NEW-BLOCKER]=2. Net change in BLOCKER count: -6 relative to run-0's 14, but the remaining 8 include the central enforcement claim, so this is architectural progress, not implementation permission.
