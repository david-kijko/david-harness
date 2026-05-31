// triage.workflow.js — deterministic root-cause-and-fix pipeline for a brownfield bug.
//
// Launch from the orchestrator (Claude main session):
//   Workflow({
//     scriptPath: "/home/david/.claude/skills/triage2/references/triage.workflow.js",
//     args: { repo, issue, lanes: 4, minConfidence: 0.7, maxRounds: 2,
//             ui_affecting: true, url: "http://localhost:3000", launch_cmd: "",
//             test_cmd: "pytest -xq backend/tests/...", typecheck_cmd: "",
//             repo_key, gotchas_path, remote,        // from references/repo-identity.sh
//             creds_file: "/run/user/1000/triage-<id>.env" } // 0600 env: LOGIN_URL/USERNAME/PASSWORD
//   })
//
// This script orchestrates ONLY. Every agent() lane is a Claude subagent that
// DISPATCHES heph2 (gpt-5.5 high) via Bash to do the real diagnosis/fix. The
// fan-out, the barrier, the confidence gate, the exa mandate, the creds gate,
// and the FIXED-only-on-verification gate all live HERE, in code — so the
// "deterministic" claim is backed by the script, not by model goodwill.

export const meta = {
  name: 'triage2-fix',
  description: 'Diagnose and fix a known brownfield bug: characterize, multi-lane heph2 root-cause diagnosis (exa enforced at low confidence), synthesize, heph2 fix in a worktree, proofshot verify, status FIXED only when verification passes',
  phases: [
    { title: 'Characterize' },
    { title: 'Diagnose' },
    { title: 'Synthesize' },
    { title: 'Fix' },
    { title: 'Verify' },
  ],
}

// ---------- inputs ----------
const REPO = args.repo
const ISSUE = args.issue
const N = args.lanes ?? 4
const MIN_CONF = args.minConfidence ?? 0.7
const EXA_CONF = 0.6                 // below this, a lane MUST have consulted exa
const MAX_ROUNDS = args.maxRounds ?? 2
const TEST_CMD = args.test_cmd ?? ''         // '' => the fix lane detects the runner
const REPO_KEY = args.repo_key ?? ''         // canonical key from repo-identity.sh
const GOTCHAS = args.gotchas_path ?? (REPO + '/Gotchas.md')
const CREDS_FILE = args.creds_file ?? ''     // secret-safe 0600 env file (preferred channel)
const TPL = '/home/david/.claude/skills/triage2/templates'
const ID = '/home/david/.claude/skills/triage2/references/repo-identity.sh'
const HEPH2 = 'HEPHAESTUS_MODEL=gpt-5.5 HEPHAESTUS_REASONING_EFFORT=high hephaestus'

// ---------- schemas ----------
const REPRO_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['summary', 'repro_cmd', 'literal_failure', 'surface', 'ui_affecting', 'launch_cmd', 'url'],
  properties: {
    summary: { type: 'string' }, repro_cmd: { type: 'string' },
    literal_failure: { type: 'string' }, surface: { type: 'string' },
    ui_affecting: { type: 'boolean' }, launch_cmd: { type: 'string' }, url: { type: 'string' },
  },
}
const HYP_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['hypotheses'],
  properties: { hypotheses: { type: 'array', minItems: 1, items: {
    type: 'object', additionalProperties: false, required: ['key', 'subsystem', 'theory'],
    properties: { key: { type: 'string' }, subsystem: { type: 'string' }, theory: { type: 'string' } } } } },
}
const LANE_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['key', 'confirmed', 'confidence', 'evidence', 'proposed_fix', 'exa_used'],
  properties: {
    key: { type: 'string' }, confirmed: { type: 'boolean' },
    confidence: { type: 'number', minimum: 0, maximum: 1 },
    evidence: { type: 'array', items: { type: 'string' } },
    proposed_fix: { type: 'string' }, exa_used: { type: 'boolean' },
  },
}
const PLAN_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['root_cause', 'fix_spec', 'confidence', 'severity', 'evidence'],
  properties: {
    root_cause: { type: 'string' }, fix_spec: { type: 'string' },
    confidence: { type: 'number', minimum: 0, maximum: 1 },
    severity: { type: 'string', enum: ['L1', 'L2', 'L3', 'L4', 'L5'] },
    evidence: { type: 'array', items: { type: 'string' } },
  },
}
const FIX_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['identity_ok', 'worktree_path', 'branch', 'head_sha', 'files_changed', 'tests', 'test_stdout', 'gotcha_appended', 'gotcha_section'],
  properties: {
    identity_ok: { type: 'boolean', description: 'true only if triage_assert_repo confirmed the worktree resolves to REPO_KEY' },
    worktree_path: { type: 'string' }, branch: { type: 'string' }, head_sha: { type: 'string' },
    files_changed: { type: 'array', items: { type: 'string' } },
    tests: { type: 'array', items: { type: 'string' } },
    test_stdout: { type: 'string', description: 'literal passing (GREEN) stdout — never fabricated' },
    gotcha_appended: { type: 'boolean' }, gotcha_section: { type: 'string', description: 'the §N appended' },
  },
}
const VERDICT_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['ran', 'pass', 'evidence'],
  properties: { ran: { type: 'boolean' }, pass: { type: ['boolean', 'null'] }, evidence: { type: 'string' } },
}

// ---------- lane prompt builders ----------
const diagnoseLane = (h, forceExa = false) => `You are a Claude subagent orchestrating ONE read-only diagnostic lane. Do NOT edit code yourself.
HYPOTHESIS key="${h.key}" subsystem="${h.subsystem}": ${h.theory}
REPO: ${REPO}
ISSUE: ${ISSUE}
REPRO: ${JSON.stringify(REPRO)}

Steps:
1. Read ${TPL}/diagnose-brief.md and fill {{REPO}} {{ISSUE}} {{HYPOTHESIS}} {{REPRO}}. Write it to a temp file.
2. Dispatch heph2 (read-only investigation):  ${HEPH2} --file <tmp-brief> --dir ${REPO} --dangerous
   Poll ~/.hephaestus/outputs/hephaestus-*.md every ~30s; read the full file when heph2 exits.
3. exa mandate: if heph2's confidence in the root cause OR fix is < ${EXA_CONF}, it MUST run
   python3 ~/.claude/skills/exa/scripts/exa_cli.py run --query "<5-whys query>" --format compact-markdown
   and cite the sources before concluding. Set exa_used accordingly — report it HONESTLY.${forceExa ? `
   ENFORCEMENT RE-DISPATCH: your prior pass returned confidence < ${EXA_CONF} with exa_used=false.
   You MUST consult exa this time before returning, or the lane will be discarded.` : ''}
4. Return LANE_SCHEMA with file:line evidence. Do NOT round up confidence.`

const synthesize = (lanes) => `You are the synthesizer. Compare these diagnostic lanes and pick the SINGLE best-supported root cause.
REPRO: ${JSON.stringify(REPRO)}
LANES: ${JSON.stringify(lanes)}
Accept a root cause ONLY if backed by traced file:line evidence a lane confirmed. Prefer strongest
evidence over highest raw confidence. Emit a fix_spec precise enough that the fix lane needs no
further investigation. Score confidence honestly (0-1) and choose a severity L1-L5.`

const fixLane = (plan) => `You are a Claude subagent orchestrating the FIX lane. Do NOT edit code yourself — heph2 does.
REPO: ${REPO}    REPO_KEY: ${REPO_KEY}    GOTCHAS: ${GOTCHAS}
ROOT CAUSE: ${plan.root_cause}
FIX SPEC: ${plan.fix_spec}
SEVERITY: ${plan.severity}
TEST_CMD: ${TEST_CMD || '(unset — detect the repo runner)'}
REPRO: ${JSON.stringify(REPRO)}

Steps:
1. Create an isolated worktree + branch off the repo's current HEAD:
   SLUG=$(echo "${plan.root_cause}" | tr ' ' '-' | tr -cd 'A-Za-z0-9-' | cut -c1-32)
   WT="\${XDG_RUNTIME_DIR:-/tmp}/triage-$SLUG"
   git -C ${REPO} worktree add "$WT" -b "triage/$SLUG"
2. MISFILE GUARD (mandatory): source ${ID}; triage_assert_repo "$WT" "${REPO_KEY}"
   If it exits non-zero, ABORT — do not run heph2, return identity_ok=false. Else identity_ok=true.
3. Read ${TPL}/fix-brief.md and fill {{WT}} {{FIX_SPEC}} {{REPRO}} {{SEVERITY}} {{TEST_CMD}} {{REPO_KEY}}.
   Write to a temp file. Dispatch heph2 against the WORKTREE (tests-first RED->GREEN; appends ONE
   Gotchas.md §N in the house format BEFORE its commit):  ${HEPH2} --file <tmp-brief> --dir "$WT" --dangerous
4. After heph2 exits, run the tests in "$WT" (${TEST_CMD || 'the runner you detected'}) and capture LITERAL stdout.
   Confirm Gotchas.md gained a new §N; capture its label and head_sha (git -C "$WT" rev-parse HEAD).
5. Return FIX_SCHEMA. Paste the real GREEN stdout into test_stdout — never fabricate it.`

const proofshotLane = (fix) => `You are a Claude subagent running the proofshot VERIFY gate on the real running app.
WORKTREE: ${fix.worktree_path}   URL: ${REPRO.url}   LAUNCH: ${REPRO.launch_cmd}
CREDS: source the 0600 env file at ${CREDS_FILE} — it defines LOGIN_URL, USERNAME, PASSWORD. Do NOT echo PASSWORD.
  set -a; . "${CREDS_FILE}"; set +a
REPRO to re-exercise: ${REPRO.repro_cmd}

Use the verified proofshot surface (start -> exec -> stop). Resolve real selectors at runtime:
  proofshot start --description "verify ${ISSUE} fixed" --url "$LOGIN_URL"${REPRO.launch_cmd ? ` --run "${REPRO.launch_cmd}"` : ''}
  proofshot exec open "$LOGIN_URL"
  proofshot exec snapshot                      # READ the accessibility tree; pick the real email/password/submit refs + a post-login marker
  proofshot exec fill <email-ref>    "$USERNAME"
  proofshot exec fill <password-ref> "$PASSWORD"   # the ACTUAL value from the env file, never a placeholder
  proofshot exec click <submit-ref>
  proofshot exec find text "<post-login marker you saw in snapshot>" first
  # re-run the exact repro path, then capture the now-working surface:
  proofshot exec screenshot proof-after.png
  proofshot stop
Return VERDICT_SCHEMA: ran=true; pass=true ONLY if the previously-failing behavior now works, with
literal evidence (artifact path + the specific assertion). pass=false with the observed failure otherwise.`

const skepticPrompt = (fix) => `Adversarially verify the fix in ${fix.worktree_path} truly resolves: ${REPRO.summary}.
Re-run the repro (${REPRO.repro_cmd}) and the tests (${JSON.stringify(fix.tests)}). Default to pass=false unless you can PROVE it.
Return VERDICT_SCHEMA with literal evidence or a concrete refutation.`

// ---------- pipeline ----------
phase('Characterize')
const REPRO = await agent(
  `You are a Claude subagent. Reproduce the issue in ${REPO} and capture the LITERAL failing output.
ISSUE: ${ISSUE}
Run the actual user-visible behavior (command, request, or page) — not a proxy. Paste the real failure.
Identify: repro_cmd, literal_failure, the broken surface, ui_affecting, launch_cmd, url.
Operator hints: ui_affecting=${args.ui_affecting}, url=${args.url}, launch_cmd=${args.launch_cmd}.
Return REPRO_SCHEMA only.`,
  { schema: REPRO_SCHEMA, phase: 'Characterize', label: 'characterize' }
)

// UI is operator-authoritative when explicitly provided; only DISCOVERED when the operator left it unset.
const UI_HINT = args.ui_affecting
const UI = (UI_HINT === true || UI_HINT === false) ? UI_HINT : REPRO.ui_affecting
const ui_downgraded = (UI_HINT === true && REPRO.ui_affecting === false)

// Fail fast: a UI fix with no upfront creds can never be verified (no mid-run prompt). Don't waste a fix lane.
if (UI && !CREDS_FILE) {
  return { status: 'BLOCKED', reason: 'ui_affecting fix requires creds_file (0600 env with LOGIN_URL/USERNAME/PASSWORD) collected in Step 0 — the background run cannot prompt for login.', repro: REPRO, ui_affecting: UI }
}

let lanes = []
let plan = null
let round = 0
const seen = new Set()
const needExa = (l) => l && l.confidence < EXA_CONF && l.exa_used === false

while (round < MAX_ROUNDS) {
  round++
  phase('Diagnose')
  const hyp = await agent(
    `Propose ${N} DISTINCT, non-overlapping root-cause hypotheses for this repro, spanning different
subsystems / failure modes. Pathology may be non-obvious — do not cluster around the first obvious guess.
Already explored (avoid repeating): ${JSON.stringify([...seen])}
REPRO: ${JSON.stringify(REPRO)}
Return HYP_SCHEMA.`,
    { schema: HYP_SCHEMA, phase: 'Diagnose', label: `hypotheses:r${round}` }
  )
  const fresh = hyp.hypotheses.filter((h) => !seen.has(h.key)).slice(0, N)
  fresh.forEach((h) => seen.add(h.key))
  if (!fresh.length) break
  const hByKey = Object.fromEntries(fresh.map((h) => [h.key, h]))

  // BARRIER: synthesis needs every lane to compare.
  let roundLanes = (await parallel(
    fresh.map((h) => () => agent(diagnoseLane(h), { schema: LANE_SCHEMA, phase: 'Diagnose', label: `diagnose:${h.key}` }))
  )).filter(Boolean)

  // ENFORCE the exa mandate in the SCRIPT: re-dispatch low-confidence lanes that skipped exa, once.
  const offenders = roundLanes.map((l, idx) => ({ l, idx })).filter(({ l }) => needExa(l))
  if (offenders.length) {
    log(`exa enforcement: re-dispatching ${offenders.length} low-confidence lane(s) that skipped exa`)
    const redo = await parallel(offenders.map(({ l }) => () =>
      agent(diagnoseLane(hByKey[l.key], true), { schema: LANE_SCHEMA, phase: 'Diagnose', label: `diagnose:${l.key}:exa` })))
    offenders.forEach(({ idx }, i) => { if (redo[i]) roundLanes[idx] = redo[i] })
  }
  const stillMissing = roundLanes.filter(needExa)
  if (stillMissing.length) log(`excluding ${stillMissing.length} lane(s) still missing mandatory exa from synthesis`)
  roundLanes = roundLanes.filter((l) => !needExa(l))

  lanes = lanes.concat(roundLanes)
  if (!lanes.length) continue

  phase('Synthesize')
  plan = await agent(synthesize(lanes), { schema: PLAN_SCHEMA, phase: 'Synthesize', label: `synthesize:r${round}` })
  log(`round ${round}: synthesized confidence=${plan.confidence} (gate ${MIN_CONF})`)
  if (plan.confidence >= MIN_CONF) break
}

if (!plan || plan.confidence < MIN_CONF) {
  return { status: 'ESCALATE', reason: `confidence ${plan?.confidence ?? 'n/a'} below gate ${MIN_CONF} after ${round} round(s)`, repro: REPRO, lanes, plan }
}

phase('Fix')
const fix = await agent(fixLane(plan), { schema: FIX_SCHEMA, phase: 'Fix', label: 'fix' })
if (fix.identity_ok === false) {
  return { status: 'BLOCKED', reason: `misfile guard: worktree did not resolve to REPO_KEY ${REPO_KEY} — refused to write a Gotcha into the wrong repo`, repro: REPRO, plan, fix }
}

phase('Verify')
const verdicts = await parallel([
  () => (UI
    ? agent(proofshotLane(fix), { schema: VERDICT_SCHEMA, phase: 'Verify', label: 'proofshot' })
    : Promise.resolve({ ran: false, pass: null, evidence: 'not ui_affecting — verified by tests + skeptic only' })),
  () => agent(skepticPrompt(fix), { schema: VERDICT_SCHEMA, phase: 'Verify', label: 'verify:skeptic' }),
])
const proofshot = verdicts[0] || { ran: false, pass: false, evidence: 'proofshot lane errored' }
const skeptic = verdicts[1] || { ran: false, pass: false, evidence: 'skeptic lane errored' }

// FIXED only when verification actually passes — the script, not prose, gates victory.
const proofshotOK = UI ? (proofshot.ran === true && proofshot.pass === true) : true
const skepticOK = skeptic.ran === true && skeptic.pass === true
const testsOK = !!(fix.test_stdout && fix.test_stdout.trim())
const verified = proofshotOK && skepticOK && testsOK && fix.gotcha_appended === true && fix.identity_ok === true
const status = verified ? 'FIXED' : 'NEEDS_REVIEW'

return {
  status,
  gates: { proofshotOK, skepticOK, testsOK, gotcha: fix.gotcha_appended, identity: fix.identity_ok },
  ui_affecting: UI, ui_downgraded,
  repro: REPRO, rounds: round, lanes, plan, fix,
  verify: { proofshot, skeptic },
  next: status === 'FIXED'
    ? 'Orchestrator: re-verify the literal stdout yourself, then git -C <repo> merge --no-ff ' + fix.branch +
      ' into the active branch; run file-gotcha.py record (key=' + REPO_KEY + ', section=' + fix.gotcha_section +
      '); then ASK the user before git worktree remove ' + fix.worktree_path + ' / git branch -d ' + fix.branch + '.'
    : 'Orchestrator: do NOT merge. Inspect verify.* + gates for the failing gate, correct, and re-run.',
}
