#!/usr/bin/env node
/**
 * superconductor — Unified CLI for autonomous spec-to-verified execution.
 *
 * One command. Connects to codex app-server via WebSocket, sends focused
 * per-wave assignments, monitors turns, runs the completion gate, and
 * loops until ALL requirements are verified. No LLM in the loop.
 *
 * Subcommands:
 *   run     <repo> --spec <file>   Full pipeline (stages 1-7 setup + worker waves)
 *   resume  <repo>                 Resume from matrix state
 *   status  <repo>                 Print current gate status
 *   gate    <repo>                 Run gate check (exit 0 = done, 1 = work remains)
 *
 * Options (run/resume):
 *   --ws <url>              App-server WebSocket (default: ws://127.0.0.1:4500)
 *   --max-waves <n>         Safety cap (default: 50)
 *   --tracks-per-wave <n>   Tracks per turn (default: 3)
 *   --model <model>         Model override
 *   --run-id <id>           Target specific run
 *   --skill-path <path>     Superconductor SKILL.md to attach
 *   --conductor-path <path> Conductor SKILL.md to attach
 *   --dry-run               Preview without executing
 *
 * Prerequisites:
 *   - codex app-server running: codex app-server --listen ws://127.0.0.1:4500
 *   - Node.js 18+ with 'ws' package: npm i -g ws
 */

import WebSocket from "ws";
import { execSync } from "node:child_process";
import { resolve, dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  existsSync, mkdirSync, appendFileSync, readFileSync,
  readdirSync, statSync, writeFileSync, copyFileSync,
} from "node:fs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const SKILL_ROOT = resolve(__dirname, "..");

// ═══════════════════════════════════════════════════════════════
//  CLI PARSER
// ═══════════════════════════════════════════════════════════════

function usage(msg) {
  if (msg) console.error(`Error: ${msg}\n`);
  console.error(`superconductor — autonomous spec-to-verified execution

Subcommands:
  run     <repo> --spec <file>   Full pipeline (setup + worker loop)
  resume  <repo>                 Resume from matrix state
  status  <repo>                 Print gate status
  gate    <repo>                 Gate check (exit 0/1)

Options (run/resume):
  --ws <url>              WebSocket URL (default: ws://127.0.0.1:4500)
  --max-waves <n>         Safety cap (default: 50)
  --tracks-per-wave <n>   Tracks per turn (default: 3)
  --model <model>         Model override
  --run-id <id>           Target specific run
  --skill-path <path>     Superconductor SKILL.md to attach
  --conductor-path <path> Conductor SKILL.md to attach
  --dry-run               Preview only`);
  process.exit(2);
}

function parseArgs() {
  const args = process.argv.slice(2);
  if (args.length < 1) usage("No subcommand provided.");

  const sub = args[0];
  if (!["run", "resume", "status", "gate"].includes(sub)) usage(`Unknown subcommand: ${sub}`);
  if (args.length < 2 || args[1].startsWith("--")) usage("No <repo> path provided.");

  const cfg = {
    subcommand: sub,
    repoRoot: resolve(args[1]),
    ws: "ws://127.0.0.1:4500",
    spec: "",
    maxWaves: 50,
    tracksPerWave: 3,
    model: null,
    dryRun: false,
    runId: "",
    skillPath: join(SKILL_ROOT, "SKILL.md"),
    conductorPath: "",
  };

  let i = 2;
  while (i < args.length) {
    switch (args[i]) {
      case "--spec":            cfg.spec = resolve(args[++i]); break;
      case "--ws":              cfg.ws = args[++i]; break;
      case "--max-waves":       cfg.maxWaves = parseInt(args[++i], 10); break;
      case "--tracks-per-wave": cfg.tracksPerWave = parseInt(args[++i], 10); break;
      case "--model":           cfg.model = args[++i]; break;
      case "--dry-run":         cfg.dryRun = true; break;
      case "--run-id":          cfg.runId = args[++i]; break;
      case "--skill-path":      cfg.skillPath = resolve(args[++i]); break;
      case "--conductor-path":  cfg.conductorPath = resolve(args[++i]); break;
      default: usage(`Unknown option: ${args[i]}`);
    }
    i++;
  }

  if (sub === "run" && !cfg.spec) usage("run requires --spec <file>");
  return cfg;
}

// ═══════════════════════════════════════════════════════════════
//  LOGGER
// ═══════════════════════════════════════════════════════════════

function createLogger(repoRoot) {
  const logDir = resolve(repoRoot, "conductor/superconductor/.logs");
  mkdirSync(logDir, { recursive: true });
  const logFile = resolve(logDir, `supervisor-${new Date().toISOString().slice(0, 10)}.log`);
  const ts = () => new Date().toISOString();
  const write = (msg) => {
    const line = `[${ts()}] ${msg}`;
    console.log(line);
    appendFileSync(logFile, line + "\n");
  };
  return {
    log: (msg) => write(msg),
    wave: (n, msg) => write(`[wave ${n}] ${msg}`),
  };
}

// ═══════════════════════════════════════════════════════════════
//  MATRIX OPERATIONS (replaces bash scripts)
// ═══════════════════════════════════════════════════════════════

function findMatrix(repoRoot, runId) {
  const scDir = join(repoRoot, "conductor/superconductor");
  if (runId) {
    const p = join(scDir, runId, "requirements-matrix.json");
    return existsSync(p) ? p : null;
  }
  if (!existsSync(scDir)) return null;
  // Most recent run
  const runs = readdirSync(scDir).filter(d => {
    const full = join(scDir, d);
    return statSync(full).isDirectory() && existsSync(join(full, "requirements-matrix.json"));
  });
  if (runs.length === 0) return null;
  runs.sort((a, b) => {
    const sa = statSync(join(scDir, a, "requirements-matrix.json")).mtimeMs;
    const sb = statSync(join(scDir, b, "requirements-matrix.json")).mtimeMs;
    return sb - sa;
  });
  return join(scDir, runs[0], "requirements-matrix.json");
}

function readMatrix(matrixPath) {
  return JSON.parse(readFileSync(matrixPath, "utf8"));
}

function tallyMatrix(data) {
  const reqs = data.requirements || [];
  const total = reqs.length;
  const by = {};
  for (const r of reqs) {
    const s = r.status || "pending";
    by[s] = (by[s] || 0) + 1;
  }
  return {
    total,
    verified: by.verified || 0,
    implemented: by.implemented || 0,
    in_track: by.in_track || by["in-track"] || 0,
    pending: by.pending || 0,
    stage: data.pipeline_stage || 0,
    runId: data.run_id || "unknown",
  };
}

function gateCheck(repoRoot, runId) {
  const matrixPath = findMatrix(repoRoot, runId);
  if (!matrixPath) return { passed: false, error: true, message: "No requirements-matrix.json found." };
  const data = readMatrix(matrixPath);
  const t = tallyMatrix(data);
  const remaining = t.total - t.verified;
  return {
    passed: remaining === 0,
    error: false,
    ...t,
    remaining,
    matrixPath,
    pct: t.total > 0 ? Math.round((t.verified * 100) / t.total) : 0,
  };
}

function readState(repoRoot, runId) {
  const matrixPath = findMatrix(repoRoot, runId);
  if (!matrixPath) {
    return { next_action: "start_fresh", stage: 0, total: 0, verified: 0, incomplete_tracks: [] };
  }

  const data = readMatrix(matrixPath);
  const t = tallyMatrix(data);

  // Find incomplete tracks
  const tracksDir = join(repoRoot, "conductor/tracks");
  const incomplete = [];
  if (existsSync(tracksDir)) {
    for (const d of readdirSync(tracksDir).sort()) {
      const plan = join(tracksDir, d, "plan.md");
      if (!existsSync(plan)) continue;
      const content = readFileSync(plan, "utf8");
      const pending = (content.match(/- \[ \]/g) || []).length;
      const inProg = (content.match(/- \[~\]/g) || []).length;
      const done = (content.match(/- \[x\]/g) || []).length;
      if (pending > 0 || inProg > 0) {
        incomplete.push({ track_id: d, pending_tasks: pending, in_progress_tasks: inProg, completed_tasks: done });
      }
    }
  }

  // Determine next action
  let next_action, message;
  if (t.total === 0) {
    next_action = "start_fresh";
    message = "Empty matrix.";
  } else if (t.pending > 0) {
    next_action = "decompose";
    message = `${t.pending} requirements not yet in tracks.`;
  } else if (t.stage < 6) {
    next_action = `resume_stage_${t.stage}`;
    message = `Resume at Stage ${t.stage}.`;
  } else if (t.in_track > 0 && incomplete.length > 0) {
    next_action = "fan_out_workers";
    message = `${t.in_track} requirements in-track. ${incomplete.length} tracks have work.`;
  } else if (t.implemented > 0) {
    next_action = "run_reviews";
    message = `${t.implemented} implemented, not yet verified.`;
  } else if (t.verified === t.total) {
    next_action = "complete";
    message = "All verified.";
  } else {
    next_action = "investigate";
    message = "Ambiguous state.";
  }

  return { next_action, message, ...t, incomplete_tracks: incomplete.slice(0, 10), matrixPath };
}

// ═══════════════════════════════════════════════════════════════
//  SCAFFOLD (replaces build-superconductor-artifacts.sh)
// ═══════════════════════════════════════════════════════════════

function scaffoldRun(repoRoot, runId) {
  const tplDir = join(SKILL_ROOT, "templates");
  const runDir = join(repoRoot, "conductor/superconductor", runId);
  mkdirSync(runDir, { recursive: true });

  if (existsSync(tplDir)) {
    for (const f of readdirSync(tplDir)) {
      const src = join(tplDir, f);
      const dst = join(runDir, f);
      if (!existsSync(dst) && statSync(src).isFile()) {
        copyFileSync(src, dst);
      }
    }
  }
  return runDir;
}

// ═══════════════════════════════════════════════════════════════
//  PROMPT TEMPLATES (string builders, no LLM)
// ═══════════════════════════════════════════════════════════════

function promptSetup(spec) {
  return `Run /conductor:superconductor with requirements source: ${spec}

Execute Stages 1 through 7 ONLY:
- Stage 1: Parse requirements into requirements-matrix.json (IDs R-001, R-002, ...)
- Stage 2: Intent alignment
- Stage 3: Code investigation
- Stage 4: Closure
- Stage 5: Sufficiency gate
- Stage 6: Decompose ALL requirements into domain tracks. Zero pending.
- Stage 7: Generate ALL track directories with spec.md, plan.md, metadata.json, index.md

STOP after Stage 7. Do NOT implement anything.
Set pipeline_stage to 7 in requirements-matrix.json.`;
}

function promptWorker(tracks, wave, total, verified) {
  const ids = tracks.map(t => t.track_id);
  const list = ids.map(id => `  - ${id}`).join("\n");
  const specs = ids.map(id =>
    `\n### Track: ${id}\nSpec: conductor/tracks/${id}/spec.md\nPlan: conductor/tracks/${id}/plan.md\nRead both. Complete ALL [ ] tasks.`
  ).join("");

  return `Wave ${wave}. ${verified}/${total} requirements verified.

ASSIGNMENT — implement these tracks to completion:
${list}

FOR EACH TRACK:
1. Read spec.md and plan.md
2. Read conductor/workflow.md for task lifecycle
3. Every task marked [ ] in the plan:
   a. Write failing tests (if TDD)
   b. Implement
   c. Run tests
   d. Mark [x] with commit SHA
   e. Commit
4. When all tasks [x]:
   - Update metadata.json status to "complete"
   - Update requirements-matrix.json: status "verified", add evidence array

Complete ALL tracks. Every [ ] becomes [x]. No exceptions.
${specs}`;
}

function promptDecompose() {
  return `Pending requirements exist in requirements-matrix.json.
Stage 6: group ALL into domain tracks. Stage 7: generate track dirs.
Zero pending after. Do NOT implement.`;
}

function promptResumeStage(n) {
  return `Resume superconductor at Stage ${n}. Complete through Stage 7. Do NOT implement.`;
}

function promptReview() {
  return `Review all "implemented" requirements. Run tests/checks. Update to "verified" with evidence. Commit.`;
}

function promptReconcile() {
  return `Matrix shows incomplete requirements but no incomplete tracks.
Read matrix + all plan.md files. Update any requirement whose track is fully [x] to "verified" with evidence. Commit.`;
}

// ═══════════════════════════════════════════════════════════════
//  WEBSOCKET CLIENT (transport only, no LLM)
// ═══════════════════════════════════════════════════════════════

class CodexClient {
  constructor(url) {
    this.url = url;
    this.ws = null;
    this.nextId = 1;
    this.pending = new Map();
    this.listeners = new Map();
    this.threadId = null;
    this.activeTurnId = null;
  }

  connect() {
    return new Promise((ok, fail) => {
      this.ws = new WebSocket(this.url);
      this.ws.on("open", ok);
      this.ws.on("error", fail);
      this.ws.on("close", (c, r) => console.error(`WS closed: ${c} ${r}`));
      this.ws.on("message", (d) => this._handle(d.toString()));
    });
  }

  _handle(raw) {
    let m;
    try { m = JSON.parse(raw); } catch { return; }
    if (m.id !== undefined && this.pending.has(m.id)) {
      const { resolve, reject } = this.pending.get(m.id);
      this.pending.delete(m.id);
      m.error ? reject(new Error(m.error.message || JSON.stringify(m.error))) : resolve(m.result);
      return;
    }
    if (m.method) {
      for (const cb of this.listeners.get(m.method) || []) cb(m.params);
    }
  }

  request(method, params) {
    const id = this.nextId++;
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.ws.send(JSON.stringify({ method, id, params }));
    });
  }

  notify(method, params) {
    this.ws.send(JSON.stringify({ method, params }));
  }

  on(m, cb) {
    if (!this.listeners.has(m)) this.listeners.set(m, new Set());
    this.listeners.get(m).add(cb);
  }

  off(m, cb) { this.listeners.get(m)?.delete(cb); }

  async init() {
    await this.request("initialize", {
      clientInfo: { name: "superconductor", title: "Superconductor", version: "2.0.0" },
    });
    this.notify("initialized", {});
  }

  async thread(config) {
    const r = await this.request("thread/start", config);
    this.threadId = r.thread.id;
    return r;
  }

  async turn(input, overrides = {}) {
    const r = await this.request("turn/start", {
      threadId: this.threadId,
      input: typeof input === "string" ? [{ type: "text", text: input }] : input,
      ...overrides,
    });
    this.activeTurnId = r.turn.id;
    return r;
  }

  steer(text) {
    if (!this.activeTurnId) return;
    this.notify("turn/steer", {
      threadId: this.threadId,
      turnId: this.activeTurnId,
      input: [{ type: "text", text }],
    });
  }

  waitDone() {
    return new Promise((resolve) => {
      const h = (p) => {
        this.off("turn/completed", h);
        this.activeTurnId = null;
        resolve(p.turn);
      };
      this.on("turn/completed", h);
    });
  }

  close() { this.ws?.close(); }
}

// ═══════════════════════════════════════════════════════════════
//  STATUS DISPLAY
// ═══════════════════════════════════════════════════════════════

function printGate(g) {
  console.log("╔══════════════════════════════════════════════╗");
  console.log("║     SUPERCONDUCTOR COMPLETION GATE           ║");
  console.log("╠══════════════════════════════════════════════╣");
  if (g.error) {
    console.log(`║ ${g.message}`);
  } else {
    console.log(`║ Run:         ${g.runId}`);
    console.log(`║ Stage:       ${g.stage}`);
    console.log(`║ Total:       ${g.total} requirements`);
    console.log(`║ Verified:    ${g.verified}`);
    console.log(`║ Implemented: ${g.implemented}`);
    console.log(`║ In-Track:    ${g.in_track}`);
    console.log(`║ Pending:     ${g.pending}`);
    console.log(`║ Remaining:   ${g.remaining}`);
    console.log("╠══════════════════════════════════════════════╣");
    if (g.passed) {
      console.log("║ ✅ GATE PASSED — All requirements verified   ║");
    } else {
      console.log(`║ ❌ GATE FAILED — ${g.remaining} of ${g.total} remain (${g.pct}% done)`);
    }
  }
  console.log("╚══════════════════════════════════════════════╝");
}

function printStatus(repoRoot, runId) {
  const state = readState(repoRoot, runId);
  const gate = gateCheck(repoRoot, runId);

  console.log("╔══════════════════════════════════════════════╗");
  console.log("║     SUPERCONDUCTOR STATUS                    ║");
  console.log("╠══════════════════════════════════════════════╣");
  console.log(`║ Next action: ${state.next_action}`);
  console.log(`║ Message:     ${state.message}`);
  console.log("╠══════════════════════════════════════════════╣");
  printGate(gate);

  if (state.incomplete_tracks.length > 0) {
    console.log("\nIncomplete tracks:");
    for (const t of state.incomplete_tracks) {
      console.log(`  ${t.track_id}: ${t.pending_tasks} pending, ${t.in_progress_tasks} in-progress, ${t.completed_tasks} done`);
    }
  }
}

// ═══════════════════════════════════════════════════════════════
//  MAIN LOOP
// ═══════════════════════════════════════════════════════════════

async function runLoop(cfg) {
  const { log, wave: logW } = createLogger(cfg.repoRoot);

  log("═══════════════════════════════════════════════");
  log("  SUPERCONDUCTOR");
  log("  Exits ONLY when ALL requirements verified.");
  log("═══════════════════════════════════════════════");
  log(`Repo:        ${cfg.repoRoot}`);
  log(`WS:          ${cfg.ws}`);
  log(`Max waves:   ${cfg.maxWaves}`);
  log(`Tracks/wave: ${cfg.tracksPerWave}`);
  log(`Spec:        ${cfg.spec || "(resume)"}`);

  // Connect
  const client = new CodexClient(cfg.ws);
  try {
    await client.connect();
  } catch {
    log(`Cannot connect to ${cfg.ws}. Start app-server first:`);
    log(`  codex app-server --listen ${cfg.ws}`);
    process.exit(2);
  }
  await client.init();
  log("Connected to app-server.");

  // Start thread
  const threadConfig = {
    cwd: cfg.repoRoot,
    approvalPolicy: "never",
    sandbox: "danger-full-access",
    ...(cfg.model ? { model: cfg.model } : {}),
  };
  await client.thread(threadConfig);
  log(`Thread: ${client.threadId}`);

  // Input builder — attaches skill(s) when needed
  const buildInput = (prompt, attachSkill = false) => {
    const arr = [{ type: "text", text: prompt }];
    if (attachSkill) {
      if (cfg.skillPath && existsSync(cfg.skillPath)) {
        arr.push({ type: "skill", name: "superconductor", path: cfg.skillPath });
      }
      if (cfg.conductorPath && existsSync(cfg.conductorPath)) {
        arr.push({ type: "skill", name: "conductor", path: cfg.conductorPath });
      }
    }
    return arr;
  };

  const send = async (prompt, n, attachSkill = false) => {
    if (cfg.dryRun) {
      logW(n, `[DRY] ${prompt.substring(0, 200)}...`);
      return { status: "completed" };
    }
    await client.turn(buildInput(prompt, attachSkill));
    logW(n, "Turn sent. Waiting for completion...");
    return client.waitDone();
  };

  // ── Setup phase (run subcommand only) ──
  if (cfg.spec) {
    log("\n── SETUP (Stages 1-7) ──");
    const t = await send(promptSetup(cfg.spec), "setup", true);
    if (t.status === "failed") {
      log(`Setup failed: ${JSON.stringify(t.error)}`);
      client.close();
      process.exit(2);
    }
    log("Setup complete.\n");
  }

  // ── Worker loop ──
  log("── WORKER LOOP ──");

  for (let w = 1; w <= cfg.maxWaves; w++) {
    // Gate check first — maybe already done
    logW(w, "Gate check...");
    const gate = gateCheck(cfg.repoRoot, cfg.runId);
    printGate(gate);

    if (gate.passed) {
      log(`\n✅ ALL REQUIREMENTS VERIFIED after ${w - 1} wave(s).`);
      client.close();
      process.exit(0);
    }

    if (gate.error) {
      log(`Gate error: ${gate.message}`);
      client.close();
      process.exit(2);
    }

    // Read state, build prompt
    const state = readState(cfg.repoRoot, cfg.runId);
    logW(w, `${state.next_action} | ${state.verified}/${state.total} verified | ${(state.incomplete_tracks || []).length} incomplete tracks`);

    let prompt;
    const act = state.next_action;

    if (act === "start_fresh") {
      if (!cfg.spec) {
        log("No run found. Use: superconductor run <repo> --spec <file>");
        client.close();
        process.exit(2);
      }
      prompt = promptSetup(cfg.spec);
    } else if (act === "decompose") {
      prompt = promptDecompose();
    } else if (act === "run_reviews") {
      prompt = promptReview();
    } else if (act === "fan_out_workers" || act === "investigate") {
      const batch = (state.incomplete_tracks || []).slice(0, cfg.tracksPerWave);
      prompt = batch.length > 0
        ? promptWorker(batch, w, state.total, state.verified)
        : promptReconcile();
    } else if (act.startsWith("resume_stage_")) {
      prompt = promptResumeStage(act.replace("resume_stage_", ""));
    } else if (act === "complete") {
      log("\n✅ ALL REQUIREMENTS VERIFIED.");
      client.close();
      process.exit(0);
    } else {
      prompt = promptReconcile();
    }

    // Send turn
    const turn = await send(prompt, w, w === 1);
    if (turn.status === "failed") {
      logW(w, `Turn failed: ${JSON.stringify(turn.error)}`);
      continue;
    }

    logW(w, "Turn complete. Looping to gate check.");
  }

  log(`\n⚠️  Safety cap (${cfg.maxWaves} waves) reached. Run 'superconductor resume' to continue.`);
  client.close();
  process.exit(1);
}

// ═══════════════════════════════════════════════════════════════
//  DISPATCH
// ═══════════════════════════════════════════════════════════════

async function main() {
  const cfg = parseArgs();

  switch (cfg.subcommand) {
    case "gate": {
      const g = gateCheck(cfg.repoRoot, cfg.runId);
      printGate(g);
      process.exit(g.passed ? 0 : g.error ? 2 : 1);
    }
    case "status": {
      printStatus(cfg.repoRoot, cfg.runId);
      process.exit(0);
    }
    case "run":
    case "resume": {
      await runLoop(cfg);
      break;
    }
  }
}

main().catch((e) => { console.error("Fatal:", e); process.exit(2); });
