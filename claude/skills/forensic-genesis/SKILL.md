---
name: forensic-genesis
description: Forensic codebase analysis with iterative validation loops. Transforms undocumented codebases into production-ready, fully documented systems through rigorous query-validate-improve cycles.
trigger: Use when user asks for "forensic code review", "genesis docs from code review", "make frontend production ready", "document this codebase", "analyze legacy code", or "/forensic-genesis"
version: 3.0.0
author: Oracle-Cortex
requires:
  - dependency-graph
  - genesis-docs
  - NotebookLM MCP (REQUIRED for validation loops)
  - Graphiti MCP (optional)
---

# Forensic Genesis Skill v2.1

**Transforms undocumented codebases into production-ready, fully documented systems.**

## Core Principle: Query-Validate-Iterate

```
┌──────────────────────────────────────────────────────────────────────┐
│  THE FUNDAMENTAL LOOP (applies to EVERY phase)                       │
│                                                                      │
│    ┌──────────┐     ┌──────────┐     ┌─────────────┐                │
│    │  UPLOAD  │────>│  QUERY   │────>│ INCORPORATE  │               │
│    │ artifact │     │ "What's  │     │ NLM answers  │               │
│    │          │     │ missing?"│     │ INTO artifact│               │
│    └──────────┘     └──────────┘     └──────┬──────┘                │
│                                             │                        │
│                                     ┌───────┴───────┐               │
│                                     │   VALIDATE    │               │
│                                     │ "Is enriched  │               │
│                                     │  version      │               │
│                                     │  complete?"   │               │
│                                     └───────┬───────┘               │
│                                             │                        │
│                              ┌──────────────┼──────────────┐        │
│                              v                             v        │
│                        ┌──────────┐                 ┌──────────┐    │
│                        │   GAPS   │                 │   PASS   │    │
│                        │ detected │                 │   gate   │    │
│                        └────┬─────┘                 └────┬─────┘    │
│                             v                            v          │
│                        ┌──────────┐               PROCEED TO        │
│                        │ IMPROVE  │               NEXT PHASE        │
│                        │ & REPEAT │               (carry NLM        │
│                        └──────────┘                insights          │
│                                                    forward)         │
│                                                                      │
│  The INCORPORATE step is what makes this forensic. Without it,      │
│  NLM answers evaporate and the loop is validation theater.          │
└──────────────────────────────────────────────────────────────────────┘
```

**THIS IS NOT OPTIONAL.** Every phase must:
1. Upload its artifacts to NotebookLM
2. Query for gaps and contradictions
3. **INCORPORATE the answers back into the artifact** (populate `notebooklm_insights[]`, add missing findings, save synthesis files)
4. Validate the enriched version
5. Iterate until validation passes
6. **Carry NLM insights forward** as inputs to subsequent phases

---

## NotebookLM: Interrogation Partner, Not Storage

NotebookLM is your **validation oracle**. After EVERY upload, you MUST query:

### Standard Validation Queries (use after EVERY artifact upload)

```
COMPLETENESS CHECK:
"Based on the [artifact] I just uploaded, what critical information is missing?
What questions remain unanswered? What would a senior engineer want to know
that isn't covered?"

CONTRADICTION CHECK:
"Are there any contradictions between [new artifact] and the previously
uploaded [codebase/findings]? List specific conflicts."

GAP ANALYSIS:
"If I had to write comprehensive documentation from this analysis,
what gaps would block me? Be specific about missing data."

QUALITY CHECK:
"On a scale of 1-10, how complete is this [artifact]? What would make it a 10?"
```

**IF GAPS ARE FOUND → FIX THEM BEFORE PROCEEDING.**

---

## Phase 0: Structure-Aware Codebase Ingestion

**Goal**: Analyze codebase structure FIRST, then ingest architecturally-segmented sources into NotebookLM so that queries hit only relevant code — not one giant dump.

**Key insight (FastCode)**: Understand structure → Navigate precisely → Load targets. Never dump the whole repo into one source. That contaminates every query with irrelevant code.

### 0.1 Structural Analysis (BEFORE any ingestion)

Run the **dependency-graph** skill to produce the architectural map:

```bash
# Invoke the dependency-graph skill on the target codebase
# This produces: dependency_graph.json, dependency_graph.dot, dependency_analysis.md
# It gives us: import graph, PageRank centrality, layer assignments,
#              bounded contexts, critical paths, and coupling scores
/dependency-graph <codebase_path> --format json,dot --output /tmp/genesis_analysis/
```

From the dependency graph output, extract:
- **Subsystem clusters** (bounded contexts / architectural layers)
- **Centrality scores** per module (PageRank — high = widely depended upon)
- **Layer assignments** (presentation / domain / infrastructure / data)
- **Critical path** modules

### 0.2 cAST Segmentation (Structure-Aware Chunking)

Segment the codebase at AST node boundaries — NOT by file or line count.

**Algorithm** (cAST = recursive split-then-merge):
1. Parse each file with tree-sitter into a full AST
2. Walk top-down: if a node fits within ~2000 tokens, emit as one chunk
3. If a node exceeds budget, recurse into children
4. Walk back up: greedily merge sibling nodes until budget is hit
5. Each chunk is a syntactically complete, self-contained unit

**Chunk size targets**:
| Purpose | Tokens | Use |
|---------|--------|-----|
| Function-level precision | 256–512 | L2 raw code chunks |
| Class-level context | 512–1024 | When function is too small to be standalone |
| Module overview | 1024–2048 | L1 summaries for ingestion |

**Grouping**: Chunks from the same subsystem cluster (from Step 0.1) are grouped together. Each subsystem becomes ONE NotebookLM source — not one source per function.

### 0.3 Generate Tiered Summaries (L0 / L1 / L2)

For each subsystem, generate three tiers:

| Tier | Size | Content | Use |
|------|------|---------|-----|
| **L0** | ~15 tokens | One sentence: what this subsystem does | Query routing signal |
| **L1** | ~2000 tokens | Public API surface, key algorithms, state, interaction contracts, identifiers exact | **NotebookLM source body** |
| **L2** | Full code | Raw code + imports + docstrings + inline comments | Deep inspection (uploaded as separate source only for high-centrality modules) |

**Build order is strictly bottom-up**:
1. **Function level**: Chunk each function with signature + decorators + docstring
2. **Class level**: Concatenate method summaries → generate class summary
3. **Module level**: Concatenate class/function summaries → generate module summary
4. **Subsystem level**: Concatenate module summaries → generate subsystem L1

**L1 generation prompt** (pass to LLM — use Gemini 3 Flash for speed):
```
Write a ~2000 token technical summary covering:
1. Public API surface (functions/classes/exports with exact signatures)
2. Core algorithm or data flow
3. Key state and side effects
4. Interaction contracts (what it needs from other subsystems, what it produces)
5. File paths for each major component
Keep all identifiers exact. Include import paths.
```

### 0.4 Create Metadata Envelope

Wrap each subsystem chunk with structured metadata as a header:

```markdown
# Subsystem: <name>
LAYER: <presentation|domain|infrastructure|data>
CENTRALITY: <PageRank score, 3 decimals>
TAGS: <auto-extracted keywords from L0>
DEPENDENCIES: <subsystems this one imports from>
DEPENDENTS: <subsystems that import from this one>
FILES: <list of file paths in this subsystem>
CRITICAL_PATH: <yes|no>

## L0 (One-liner)
<single sentence summary>

## L1 (Core Procedure)
<~2000 token technical summary>
```

### 0.5 Ingest into NotebookLM (Per-Subsystem Sources)

**Create one NotebookLM source per subsystem** — NOT one giant dump:

```
# For EACH subsystem identified in Step 0.1:
notebook_add_text({
  notebook_id: "<id>",
  text: "<metadata envelope + L1 from Step 0.4>",
  title: "L1-subsystem-<name>-<layer>"
})

# For HIGH-CENTRALITY modules only (PageRank > 0.1):
# Also upload L2 (full code) as separate source for deep inspection
notebook_add_text({
  notebook_id: "<id>",
  text: "<full code for this module>",
  title: "L2-module-<name>-full-source"
})
```

**Also upload structural artifacts**:
```
# The dependency graph itself (enables architecture questions)
notebook_add_text({
  notebook_id: "<id>",
  text: "<dependency_analysis.md from Step 0.1>",
  title: "L1-architecture-dependency-graph"
})

# Shared utilities / cross-cutting concerns — separate source
notebook_add_text({
  notebook_id: "<id>",
  text: "<L1 summary of shared/, utils/, common/ code>",
  title: "L1-shared-utilities-cross-cutting"
})
```

### 0.6 Validate Ingestion (MANDATORY)

```
notebook_query({
  notebook_id: "<id>",
  query: "List all subsystems/modules that have been uploaded as sources.
         For each, state: what it does, what layer it belongs to, and
         what it depends on. Also identify any subsystems that seem
         incomplete or suspiciously thin."
})
```

**GATE CHECK:**
- [ ] NotebookLM can identify each subsystem by name
- [ ] Layer assignments match the dependency graph
- [ ] Dependencies between subsystems are understood
- [ ] No subsystem was silently truncated or lost
- [ ] High-centrality modules have both L1 and L2 sources

**IF VALIDATION FAILS:** Re-segment the failing subsystem, re-upload, re-validate.

### 0.7 Build Query Routing Index (for Phases 2-4)

Save the L0 summaries as a local routing index — this tells the agent WHICH subsystem sources to scope future NotebookLM queries to:

```
# Save to genesis_spec/routing_index.md
# Format:
# | Subsystem | Layer | L0 Summary | NotebookLM Source Title | Centrality |
# |-----------|-------|------------|------------------------|------------|
# | auth      | domain | Handles JWT issuance and session management | L1-subsystem-auth-domain | 0.847 |
# | api       | presentation | REST endpoints for user and product CRUD | L1-subsystem-api-presentation | 0.623 |
```

**Query routing rules for subsequent phases:**
- Architecture questions → scope to: dependency-graph source + all L1 subsystem sources
- Security questions → scope to: high-centrality L2 sources + infrastructure layer
- Code quality questions → scope to: L1 sources in the relevant layer only
- Business logic questions → scope to: domain-layer L1 sources only
- Cross-cutting questions → scope to: shared-utilities source + relevant subsystem sources

**The routing index is a REQUIRED INPUT to Phase 2 agents.** Each agent receives the routing index and MUST specify which subsystem sources it is querying against — no more querying the entire notebook indiscriminately.

---

## Phase 1: Tech Stack Discovery + Validation

**Goal**: Understand AND verify understanding of technology landscape.

### 1.1 Detect Stack
Analyze package.json, config files, imports to identify:
- Framework(s)
- Build tools
- Dependencies
- Patterns

### 1.2 Upload Discovery to NotebookLM
```
notebook_add_text({
  notebook_id: "<id>",
  text: "<tech stack findings as markdown>",
  title: "Analysis: Tech Stack Discovery"
})
```

### 1.3 VALIDATE DISCOVERY (MANDATORY)
```
notebook_query({
  notebook_id: "<id>",
  query: "Compare the tech stack analysis against the actual codebase.
         Are there any technologies used in the code that weren't identified?
         Are there any identified technologies that don't appear in the code?
         What's the confidence level of this analysis?"
})
```

**GATE CHECK:**
- [ ] All major technologies identified
- [ ] No false positives (claimed tech not actually used)
- [ ] Version numbers accurate where specified

**IF GAPS FOUND:** Research missing technologies, update analysis, re-upload, re-validate.

---

## Phase 2: Multi-Agent Code Review + Validation Loop

**Goal**: Comprehensive analysis with cross-validation between agents.

### 2.1 Deploy 6 Review Agents (with Routing Index)

Each agent receives the **routing index** from Phase 0.7 and MUST scope its NotebookLM queries to relevant subsystem sources only. This prevents context contamination where irrelevant code pollutes answers.

| Agent | Output | Focus | Query Scope (from routing index) |
|-------|--------|-------|----------------------------------|
| Architecture Analyzer | `01_architecture.json` | Structure, patterns, dependencies | All L1 sources + dependency graph |
| Code Quality Reviewer | `02_code_quality.json` | Smells, complexity, maintainability | Per-layer L1 sources (iterate layer by layer) |
| Security Auditor | `03_security.json` | Vulnerabilities, secrets, auth | High-centrality L2 sources + infrastructure layer |
| Orphan Detective | `04_orphans.json` | Dead code, stubs, unused features | All L1 sources + shared-utilities |
| Frontend Readiness Assessor | `05_frontend_readiness.json` | API calls, mock data, state | Presentation + domain L1 sources |
| JTBD Mapper | `06_jtbd.json` | User flows, features, business logic | Domain-layer L1 sources only |

### 2.2 Upload EACH Finding + Validate + INCORPORATE

**FOR EACH AGENT (do not batch):**

```
# Step 1: Upload
notebook_add_text({
  notebook_id: "<id>",
  text: "<agent findings JSON as markdown>",
  title: "Findings: <Agent Name>"
})

# Step 2: Validate
VALIDATION_RESPONSE = notebook_query({
  notebook_id: "<id>",
  query: "Review the <Agent Name> findings against the codebase:
         1. Are there findings that contradict the code?
         2. Are there obvious issues in the code NOT captured in findings?
         3. Are severity levels appropriate?
         4. What's missing from this analysis?"
})

# Step 3: INCORPORATE (MANDATORY — this is the step agents skip)
# The validation response IS intelligence. It MUST flow back into the findings.
#
# a) Populate the notebooklm_insights[] array in the findings JSON:
findings["notebooklm_insights"].append({
  "query": "<the validation query>",
  "response": "<FULL NotebookLM response — do NOT summarize>",
  "relevance_score": <0.0-1.0>
})

# b) For each issue NotebookLM identified as MISSING, create a new finding entry:
#    - Set id: "<AGENT_PREFIX>-NLM-001" (NLM = NotebookLM-surfaced)
#    - Set source: "notebooklm_validation" in tags
#    - Include the original NotebookLM quote as evidence
#    These are REAL findings. NotebookLM has the full codebase. Its gaps ARE your gaps.

# c) For each severity disagreement, UPDATE the severity with a note:
#    - Add "severity_adjusted_by: notebooklm_validation" to tags
#    - Log original vs adjusted severity in description

# Step 4: Re-upload the ENRICHED findings (now includes NLM insights + new findings)
notebook_add_text({
  notebook_id: "<id>",
  text: "<ENRICHED agent findings with NLM insights>",
  title: "Findings: <Agent Name> (Enriched)"
})
```

**GATE CHECK (per agent):**
- [ ] Findings reference real file paths
- [ ] Severity levels are justified
- [ ] No major issues missed
- [ ] Recommendations are actionable
- [ ] `notebooklm_insights[]` is populated (not empty)
- [ ] Any NLM-surfaced gaps are added as findings with `NLM-` prefix

**IF GAPS FOUND:** Agent re-analyzes specific areas, updates findings, re-uploads.

**WHY THIS MATTERS:** Without Step 3, NotebookLM's answers are wasted context. The agent asks "what's missing?" — NotebookLM says "you missed X, Y, Z" — and the agent just... checks a gate and moves on. X, Y, Z never appear in the findings. This is the #1 failure mode of this skill.

### 2.3 Cross-Agent Validation + Synthesis Artifact (MANDATORY)

After all 6 agents complete:

```
# Step 1: Cross-reference query
CROSS_VALIDATION = notebook_query({
  notebook_id: "<id>",
  query: "Cross-reference all 6 agent findings:
         1. Do any agents contradict each other?
         2. Are there blind spots (areas no agent covered)?
         3. Do severity assessments align across agents?
         4. What's the overall coherence of this analysis?
         5. What are the top 5 issues that MULTIPLE agents flagged independently?"
})

# Step 2: SAVE as durable artifact (MANDATORY — this answer is gold)
# Write the full cross-validation response to a file:
#   genesis_spec/findings/00_cross_validation_synthesis.md
#
# Structure:
#   ## Contradictions
#   <from NotebookLM response>
#   ## Blind Spots
#   <from NotebookLM response>
#   ## Severity Alignment
#   <from NotebookLM response>
#   ## Convergent Issues (flagged by multiple agents)
#   <from NotebookLM response>
#   ## Overall Coherence Assessment
#   <from NotebookLM response>
#
# This file becomes a REQUIRED INPUT to Phase 3 and Phase 4.

# Step 3: Upload the synthesis back to NotebookLM as its own source
notebook_add_text({
  notebook_id: "<id>",
  text: "<cross-validation synthesis markdown>",
  title: "Synthesis: Cross-Agent Validation"
})
```

**IF CONTRADICTIONS:** Resolve conflicts, update affected findings, re-validate.

**WHY THIS IS SAVED:** The cross-validation synthesis is the single most valuable artifact NotebookLM produces — it sees ALL findings against the FULL codebase simultaneously. Without saving it, this intelligence evaporates and Phase 3/4 regenerate it from scratch (badly).

---

## Phase 3: Insight Synthesis + Deep Validation

**Goal**: Extract deeper insights AND verify they're grounded in evidence.

### 3.0 Hybrid Retrieval Weighting (Query Scope Strategy)

Different question types require different source scoping. Use the routing index from Phase 0.7 and these empirically-validated weighting ratios (from DKB benchmark, 2025):

| Query Domain | AST/Graph Sources | Semantic (L1) Sources | Keyword (BM25-like) |
|---|---|---|---|
| **Architecture** | 60% — All L1 + dependency graph | 30% — Subsystem summaries | 10% — Specific identifier names |
| **Security** | 35% — Infrastructure L2 + taint paths | 25% — Domain L1 sources | 40% — CVE IDs, dangerous API names, exact patterns |
| **Code Quality** | 20% — Coupling/cohesion from dep graph | 50% — Per-layer L1 sources | 30% — Smell pattern names, metric thresholds |
| **Business Logic** | 15% — Domain layer call graph | 55% — Domain + JTBD L1 sources | 30% — Feature names, user-facing terms |

**In practice**: This means the Architecture Analyzer agent queries the dependency graph source + all L1 subsystem sources, while the Security Auditor focuses on high-centrality L2 sources + infrastructure layer + exact CVE/CWE pattern matching.

### 3.1 Query for Insights

Ask NotebookLM targeted questions (scoped to relevant sources per routing index):

```
# Architecture insights
"What are the 3 biggest architectural risks in this codebase?"
"If this system scaled 10x, what would break first?"

# Security insights
"What's the most likely attack vector for this application?"
"If I was a malicious actor, how would I exploit this code?"

# Business insights
"What user problems does this code solve?"
"What features appear half-implemented?"

# Integration insights
"What does the backend need to provide for this frontend?"
"What API contracts can we infer from the frontend code?"
```

### 3.2 Validate Insights Against Evidence

**FOR EACH INSIGHT:**

```
notebook_query({
  notebook_id: "<id>",
  query: "I concluded that [INSIGHT].
         Show me the specific code evidence that supports this.
         Also show me any code that contradicts this conclusion."
})
```

**GATE CHECK:**
- [ ] Every insight has code evidence
- [ ] No insight is contradicted by code
- [ ] Insights are non-obvious (not just restating findings)

**IF INSIGHT UNSUPPORTED:** Remove or refine the insight, document uncertainty.

### 3.3 Gap Analysis (CRITICAL)

```
notebook_query({
  notebook_id: "<id>",
  query: "I'm about to write 12 sections of documentation. Based on
         everything uploaded so far, what information am I missing?
         What questions can I NOT answer with current analysis?
         Be exhaustive - list every gap."
})
```

**ALL GAPS MUST BE ADDRESSED BEFORE PHASE 4.**

---

## Phase 4: Genesis Documentation + Iterative Validation

**Goal**: Transform findings into documentation with per-section validation.

### The 12 Genesis Sections

| # | Section | Primary Sources | Validation Query |
|---|---------|-----------------|------------------|
| 01 | Introduction & Executive Summary | JTBD, Architecture | "Does this summary accurately represent the codebase?" |
| 02 | Product Requirements | JTBD, Frontend Readiness | "Are all features from the code captured as requirements?" |
| 03 | Technology Stack | Phase 1 discovery | "Is the tech stack description accurate and complete?" |
| 04 | Process Flowcharts | Architecture, JTBD | "Do these flows match the actual code paths?" |
| 05 | Architecture Design | Architecture findings | "Does this architecture diagram reflect the real code?" |
| 06 | Data Models | Frontend Readiness | "Are these data models consistent with the code's types?" |
| 07 | Security & Compliance | Security findings | "Are all security issues from findings addressed here?" |
| 08 | Testing Strategy | Code Quality | "Is this test strategy appropriate for this codebase?" |
| 09 | Monitoring & Observability | Code Quality | "Does this monitoring plan cover the code's needs?" |
| 10 | Deployment & Operations | Build configs | "Is the deployment section accurate to the build setup?" |
| 11 | Documentation & Knowledge | All | "What's still undocumented after this section?" |
| 12 | Reference Collections | Raindrop, Context7 | "Are all referenced docs relevant and current?" |

### Section Generation Protocol (FOR EACH SECTION)

```
1. GATHER SOURCES — Before writing a single word, assemble these inputs:
   a) Primary findings JSON (from the table above)
   b) notebooklm_insights[] from each relevant findings file
      — These contain NotebookLM's gap analysis, missed issues, severity adjustments
   c) 00_cross_validation_synthesis.md (the cross-agent synthesis from Phase 2.3)
   d) Phase 3 insight responses (the evidence-grounded insights)

   IF any of (b), (c), or (d) are empty or missing → STOP.
   You skipped incorporation in Phase 2/3. Go back and fix it.

2. GENERATE section from ALL gathered sources
   — The section MUST reference NotebookLM-surfaced findings (NLM-* prefixed)
   — The section MUST incorporate cross-validation blind spots
   — If NotebookLM identified an issue that no agent caught,
     it MUST appear in the relevant section (not just the validation log)

3. UPLOAD to NotebookLM:
   notebook_add_text({
     notebook_id: "<id>",
     text: "<section content>",
     title: "Genesis: Section XX - <Name>"
   })

4. VALIDATE against codebase AND against NotebookLM's own prior answers:
   notebook_query({
     notebook_id: "<id>",
     query: "<Section-specific validation query from table above>
            Also: does this section address the gaps and blind spots
            you identified during the code review validation phase?
            List any of YOUR prior recommendations that are missing
            from this section."
   })

5. CHECK for completeness:
   notebook_query({
     notebook_id: "<id>",
     query: "What's missing from Section XX that should be there?
            What claims in this section lack evidence?"
   })

6. IF GAPS → Revise section, re-upload, re-validate
7. IF CLEAN → Proceed to next section
```

**NEVER BATCH SECTIONS.** Each must validate before the next begins.

**THE CRITICAL DISTINCTION:** Step 1 is what makes this forensic. Without it, you're generating documentation from raw findings alone — ignoring the entire NotebookLM interrogation that happened in Phase 2 and 3. That interrogation surfaced issues, contradictions, and blind spots that the raw findings missed. If those don't appear in the final docs, the entire validation loop was theater.

### 4.2 Generate Dependency Visualizations

```bash
# Generate DOT file
/dependency-graph <codebase_path> --format dot --output visualizations/

# Upload and validate
notebook_add_text({
  notebook_id: "<id>",
  text: "<dependency graph description>",
  title: "Visualization: Dependency Graph"
})

notebook_query({
  notebook_id: "<id>",
  query: "Does this dependency graph accurately reflect the import
         relationships in the codebase? What's missing?"
})
```

---

## Phase 5: Final Report + Comprehensive Validation

**Goal**: Create actionable reports AND verify they're actionable.

### 5.1 Generate Reports

- `EXECUTIVE_SUMMARY.md`
- `FRONTEND_READINESS_REPORT.md`
- `CLEANUP_CHECKLIST.md`

### 5.2 Upload and Validate Each Report

```
notebook_add_text({
  notebook_id: "<id>",
  text: "<report content>",
  title: "Report: <Name>"
})

notebook_query({
  notebook_id: "<id>",
  query: "Review this report for:
         1. Accuracy - do claims match the code?
         2. Actionability - can someone actually execute these recommendations?
         3. Completeness - what's missing that should be in this report?
         4. Priority - are items correctly prioritized?"
})
```

### 5.3 FINAL VALIDATION (MANDATORY)

```
notebook_query({
  notebook_id: "<id>",
  query: "I've completed the forensic genesis analysis. Review ALL uploaded
         artifacts (codebase, findings, sections, reports) and answer:

         1. What questions about this codebase remain UNANSWERED?
         2. What contradictions exist between documents?
         3. If a new developer read only these docs, what would confuse them?
         4. What's the single biggest gap in this analysis?
         5. On a scale of 1-10, how production-ready is this documentation?"
})
```

**GATE CHECK:**
- [ ] Score ≥ 8/10
- [ ] No critical unanswered questions
- [ ] No contradictions
- [ ] All major paths documented

**IF SCORE < 8:** Address identified gaps, regenerate affected documents, re-validate.

---

## Output Files (VERIFIED)

```
genesis_spec/
├── structure/                     # Phase 0 outputs (REQUIRED by all subsequent phases)
│   ├── dependency_graph.json      ✓ Full graph with centrality, layers, clusters
│   ├── dependency_graph.dot       ✓ GraphViz visualization
│   ├── dependency_analysis.md     ✓ Written architectural insights
│   ├── routing_index.md           ✓ L0 summaries → NotebookLM source mapping (REQUIRED by Phase 2 agents)
│   └── subsystems/                # Per-subsystem L1 summaries (what was uploaded to NLM)
│       ├── auth-domain.md         ✓ L1 metadata envelope
│       ├── api-presentation.md    ✓ L1 metadata envelope
│       └── ...                    ✓ One per subsystem
│
├── findings/                      # All validated + enriched with NLM insights
│   ├── 00_cross_validation_synthesis.md  ✓ Phase 2.3 cross-agent NLM synthesis (REQUIRED by Phase 4)
│   ├── 01_architecture.json       ✓ Uploaded + validated + notebooklm_insights[] populated
│   ├── 02_code_quality.json       ✓ Uploaded + validated + notebooklm_insights[] populated
│   ├── 03_security.json           ✓ Uploaded + validated + notebooklm_insights[] populated
│   ├── 04_orphans.json            ✓ Uploaded + validated + notebooklm_insights[] populated
│   ├── 05_frontend_readiness.json ✓ Uploaded + validated + notebooklm_insights[] populated
│   └── 06_jtbd.json               ✓ Uploaded + validated + notebooklm_insights[] populated
│
├── section_guides/                # All validated
│   ├── {Project}_Section_01_Introduction.md          ✓
│   ├── {Project}_Section_02_Product_Requirements.md  ✓
│   ├── {Project}_Section_03_Technology_Stack.md      ✓
│   ├── {Project}_Section_04_Process_Flowcharts.md    ✓
│   ├── {Project}_Section_05_Architecture_Design.md   ✓
│   ├── {Project}_Section_06_Data_Models.md           ✓
│   ├── {Project}_Section_07_Security_Compliance.md   ✓
│   ├── {Project}_Section_08_Testing_Strategy.md      ✓
│   ├── {Project}_Section_09_Monitoring_Observability.md ✓
│   ├── {Project}_Section_10_Deployment_Operations.md ✓
│   ├── {Project}_Section_11_Documentation.md         ✓
│   └── {Project}_Section_12_Reference_Collections.md ✓
│
├── visualizations/                # All validated
│   ├── dependency_graph.dot       ✓
│   ├── dependency_graph.json      ✓
│   └── dependency_graph.html      ✓ (if graphviz available)
│
├── EXECUTIVE_SUMMARY.md           ✓ Validated
├── FRONTEND_READINESS_REPORT.md   ✓ Validated
├── CLEANUP_CHECKLIST.md           ✓ Validated
└── VALIDATION_LOG.md              # NEW: Record of all validation queries/responses
```

---

## Validation Log (NEW)

Every validation query and response must be logged:

```markdown
# Validation Log

## Phase 0: Ingestion
- Query: "List the 10 most important files..."
- Response: [summary]
- Gate: PASS/FAIL
- Action taken: [if any]

## Phase 2: Agent - Architecture
- Query: "Review findings against codebase..."
- Response: [summary]
- Gaps found: [list]
- Action taken: [what was fixed]
- Re-validation: PASS

[... continues for every validation ...]

## Final Score: X/10
## Total iterations: N
## Unresolved gaps: [list if any]
```

---

## Failure Modes to Avoid

| Anti-pattern | Why it's wrong | Correct approach |
|--------------|----------------|------------------|
| Batch uploading | Can't validate individual artifacts | Upload one, validate, proceed |
| Skipping validation queries | Produces unchecked garbage | Every upload gets queried |
| Accepting first response | May have gaps | Iterate until PASS |
| Proceeding despite gaps | Downstream docs will be wrong | FIX GAPS before proceeding |
| NotebookLM as storage | Wastes the validation capability | Query after EVERY upload |
| Linear execution | No feedback → no improvement | Loop until validated |
| **Query-then-discard** | **#1 failure mode.** NLM answers never enter findings or docs | **INCORPORATE: merge NLM answers into findings JSON, save synthesis as file, use as source in Phase 4** |
| Empty `notebooklm_insights[]` | Template has the field but agent never fills it | Populate after EVERY validation query — full response, not summary |
| Generating docs from raw findings only | Ignores everything NLM surfaced in Phases 2-3 | Phase 4 Step 1 REQUIRES gathering NLM insights + cross-validation synthesis BEFORE writing |

---

## Quality is Non-Negotiable

The old skill had a "Quality Gates" checklist at the end. That's backwards.

**Quality is enforced CONTINUOUSLY, not checked at the end.**

Every artifact must be:
1. Uploaded to NotebookLM
2. Queried for gaps
3. Improved if gaps found
4. Re-validated
5. Logged

**There is no "skip validation" option.** If NotebookLM is unavailable, the skill cannot proceed - find another notebook or create one.

---

## Session Handoff

If context limit approaches:

```markdown
# Forensic Genesis Handoff

## Current Phase: X
## Last Validated Artifact: <name>
## Validation Status:
- Phase 0: PASS
- Phase 1: PASS
- Phase 2: IN_PROGRESS (4/6 agents validated)

## Next Actions:
1. Validate agent 5 findings
2. Validate agent 6 findings
3. Cross-agent validation
4. Proceed to Phase 3

## NotebookLM Notebook ID: <id>
## Files Created: [list]
## Gaps Identified: [list]
```

Save to `~/.cortex/checkpoints/` and Graphiti before ending session.

---

**Version**: 3.0.0
**Author**: Oracle-Cortex
**Status**: Requires Validation Loops + Incorporation Discipline + Structure-Aware Ingestion

**Changelog v3.0** (FastCode integration):
- Phase 0 completely replaced: naive repomix dump → structure-aware ingestion pipeline
- Added: dependency-graph skill as prerequisite for structural analysis (Step 0.1)
- Added: cAST segmentation — chunks at AST boundaries, not file/line boundaries (Step 0.2)
- Added: L0/L1/L2 tiered summaries per subsystem (Step 0.3)
- Added: metadata envelopes with layer, centrality, dependencies, tags (Step 0.4)
- Added: per-subsystem NotebookLM sources instead of one giant dump (Step 0.5)
- Added: query routing index — agents scope NLM queries to relevant sources only (Step 0.7)
- Phase 2.1: agents now receive routing index and must declare which sources they query
- New output directory: `genesis_spec/structure/` for Phase 0 artifacts
- Research basis: Perplexity research on cAST (CMU/Augment), DKB graph RAG benchmarks, hybrid retrieval weighting ratios, context contamination prevention patterns

**Changelog v2.1**: Fixed "query-then-discard" anti-pattern — NLM answers now flow back into findings (Phase 2.2 Step 3), cross-validation saved as durable artifact (Phase 2.3 Step 2), and Phase 4 section generation explicitly consumes NLM insights as source material (Step 1 GATHER SOURCES).
