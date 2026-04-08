---
name: kijko-hygiene
description: Use when working in any Kijko repository (kijko-platform, HyperVisa, Panopticon), creating branches, making commits, opening PRs, managing worktrees, or when unsure about Linear ticket workflow, RACI responsibilities, or code review requirements
---

# Kijko GitHub Hygiene Standard

Enforces Kijko's two core protocols: GitHub Hygiene and RACI Responsibility Matrix. Every branch, commit, PR, and worktree must follow these rules.

## Repositories

| Repo | Purpose | Main | Develop |
|------|---------|------|---------|
| **kijko-platform** | Core SaaS (Sandra, Skills, Habits, Reflexes) | `main` | `develop` |
| **HyperVisa** | Core IP — Video-Mediated Context Engine | `main` | `develop` |
| **Panopticon** | Monitoring, observability, dashboards | `main` | `develop` |

**HyperVisa is classified as core IP.** All HyperVisa PRs require David's explicit approval. No exceptions.

## Branch Naming

**Format:** `<type>/<LINEAR-ID>-<short-description>`

| Prefix | Purpose | Example |
|--------|---------|---------|
| `feature/` | New feature | `feature/KIJ-142-sandbox-metrics` |
| `fix/` | Bug fix | `fix/KIJ-203-auth-token-refresh` |
| `hotfix/` | Urgent production fix | `hotfix/KIJ-301-critical-rls-bypass` |
| `improvement/` | Refactoring / optimization | `improvement/KIJ-88-query-perf` |
| `release/` | Release preparation | `release/v1.3.0` |
| `prd/` | PRD bundle (multiple tickets) | `prd/KIJ-400-sandra-engine-v2` |
| `research/` | R&D exploration (David only) | `research/KIJ-500-hypervisa-swarm-v2` |

**Naming rules:**
1. Always include Linear ticket ID (`KIJ-NNN`)
2. Lowercase, hyphen-separated
3. 3-5 word descriptions
4. No trailing hyphens, no double hyphens, no underscores/spaces/punctuation
5. Alphanumeric and hyphens only
6. `research/` branches are human-only (David). NEVER create research/ branches as an agent.

**Never push directly to `main` or `develop`.** All changes arrive via Pull Requests.

## Worktree Protocol

**Directory structure:** All worktrees are siblings to the bare clone.

```
~/kijko/
  kijko-platform.git/                          # Bare repo
  kijko-platform--main/                        # main worktree
  kijko-platform--develop/                     # develop worktree
  kijko-platform--feature-KIJ-142-sandbox-metrics/  # Feature worktree
```

**Naming:** `<repo-name>--<branch-name-with-hyphens>`

**Lifecycle:**
1. Create worktree when starting a ticket or PRD
2. Initialize (run setup: `npm install`, `bundle install`, etc.)
3. Work exclusively within the worktree for that ticket
4. Clean up after merge — commit, then remove worktree
5. Don't hoard worktrees

**Commands:**
```bash
# Create worktree
cd kijko-platform.git
git worktree add ../kijko-platform--feature-KIJ-142-sandbox-metrics feature/KIJ-142-sandbox-metrics

# List / Remove / Prune
git worktree list
git worktree remove ../kijko-platform--feature-KIJ-142-sandbox-metrics
git worktree prune
```

## Workflow Scenarios

### Scenario A: Single Ticket (Default)

`1 Linear ticket = 1 branch = 1 worktree = 1 PR`

Linear auto-transitions: Backlog -> In Progress -> In Review -> Done

**Use when:** scope < 1 day, standalone, any engineer. **Default to this.**

### Scenario B: PRD Bundle (Exception)

Multiple related tickets bundled into one branch/PR.

**Rules:**
1. Create parent Linear ticket as anchor
2. Link all child tickets as sub-issues in Linear
3. Use `prd/` branch prefix
4. PR description MUST list every Linear ticket ID (magic words)
5. Update each child ticket status manually when sub-work begins
6. All child tickets close together when PRD PR is merged

**Use when:** multi-day, multi-component, tightly coupled changes.

### Scenario C: R&D Research (David Only)

Uses `research/` prefix, longer lifecycle, weekly rebase against `develop`, no direct merge to `main`. Research flows through `develop` via PR.

## Linear <-> GitHub Sync

| Step | Action | Linear Status | Who |
|------|--------|---------------|-----|
| 1 | Pick up ticket | -> **In Progress** | Developer |
| 2 | Create branch with ticket ID | (auto-detected) | Developer / Agent |
| 3 | Create worktree | — | Developer / Agent |
| 4 | Commit with ticket ID in message | — | Developer / Agent |
| 5 | Open PR with ticket ID in title | -> **In Review** | Developer / Agent |
| 6 | PR approved & merged to `develop` | -> **Done** | Reviewer |
| 7 | Remove worktree, delete branch | — | Developer / Agent |

## Commit Message Format

```
KIJ-<number>: <imperative verb> <what changed>

- Detail bullet 1
- Detail bullet 2
```

**Rules:**
- Always prefix with Linear ticket ID: `KIJ-NNN: description`
- Keep first line under 72 characters
- Use imperative mood ("Add feature" not "Added feature")

## PR & Code Review

**Flow:** `feature branch -> develop (1 approval) -> main (David OR Tijmen approval) -> Production`

**HyperVisa:** `research/ -> develop (David approval, mandatory) -> main (David approval, mandatory)`

**PR Checklist (include in every PR):**
- [ ] Branch name follows convention: `<type>/KIJ-<num>-<desc>`
- [ ] All Linear tickets referenced in PR description
- [ ] All tests pass locally
- [ ] No secrets or credentials committed
- [ ] Worktree cleaned up after merge
- [ ] If HyperVisa repo: David has explicitly approved

**PR rules:**
- Always include Linear ticket ID in PR title
- For PRD bundles: list ALL child ticket IDs in PR description
- Target: `develop` (never `main` directly)

## Agent Boundaries

```
- NEVER modify HyperVisa core engine files without explicit David approval
- NEVER modify Canon, Trinity, or Agent Smith subsystems autonomously
- NEVER commit secrets, API keys, or .env files
- NEVER force push to main or develop
- NEVER merge your own PR without review
- ASK FIRST before making architectural changes
```

## RACI Quick Reference

**R**=Responsible, **A**=Accountable, **C**=Consulted, **I**=Informed

**Team:** T=Tijmen (CEO), D=David (CTO), I=Indy (Engineer)

| Task | D | T | I |
|------|---|---|---|
| Architecture decisions | A | C | I |
| PRD creation & scope | C | A | I |
| Feature implementation | A | I | R |
| Bug fixes (non-critical) | I | I | R |
| Hotfix (production) | A/R | I | R |
| Code review & PR approval | R | I | R |
| Branch creation & naming | I | I | R |
| Worktree management | I | I | R |
| Linear backlog grooming | C | A | R |
| Linear ticket status updates | I | I | R |
| PRD bundle scoping | A | C | R |
| Agent system prompt updates | A | I | C |
| CI/CD pipeline changes | A | I | R |
| Production deployment (main) | A | I | R |
| Security & credentials | A | C | I |
| Approve HyperVisa PR (any) | A (mandatory) | I | — |

## RICE Prioritization

**Score = (Reach x Impact x Confidence) / Effort**

For moat-critical work (HyperVisa R&D, competitive response): **Impact weighted 2x.**

| Decision Type | RICE Scorer | Approver |
|---------------|-------------|----------|
| Product features | Tijmen | Tijmen |
| Tech debt / infra | David | David |
| HyperVisa R&D | David | David |
| Competitive response | David (tech) + Tijmen (market) | Tijmen |
| Bug fixes | Indy (proposes) | David (approves) |

## Escalation Protocol

| Situation | Action | Who Decides |
|-----------|--------|-------------|
| Linear ticket unclear | Comment, tag Tijmen | Tijmen (A) |
| PRD scope creep | Flag in standup | Tijmen (A) + David (C) |
| Branch naming violation in CI | Fix immediately before merge | Developer (R) |
| Agent producing non-compliant branches | Update agent system prompt | David (A) |
| Production incident | Hotfix branch immediately | David (A) + nearest R |
| Linear backlog diverged from repos | Audit and reconcile in next standup | Tijmen (A), Indy (R) |
| David over-allocated to impl work | Flag to Tijmen, adjust sprint scope | Tijmen (A) |
| Competitor launches threatening feature | Emergency assessment + R&D sprint | David (R), Tijmen (A) |

## The Golden Rules

1. Never push directly to `main` or `develop`
2. Every branch has a Linear ticket ID
3. Every worktree gets cleaned up after merge
4. PRD bundles use `prd/` prefix and list all child tickets
5. R&D uses `research/` prefix — David only
6. AI agents can propose code, never own it — all agent PRs require human review
7. When in doubt, default to single-ticket workflow
8. Keep Linear honest — if it's not in Linear, it didn't happen
9. HyperVisa PRs require David's explicit approval — no exceptions
10. Protect David's R&D time — it's what keeps us ahead

## Pre-commit Hook

Branch name validation (install in `.githooks/pre-commit`):

```bash
#!/usr/bin/env bash
branch_name=$(git rev-parse --abbrev-ref HEAD)
valid_regex='^(feature|fix|hotfix|improvement|release|prd|research)/KIJ-[0-9]+-[a-z0-9-]+$|^(main|develop)$'
if [[ ! $branch_name =~ $valid_regex ]]; then
  echo "ERROR: Branch name '$branch_name' does not follow Kijko convention."
  echo "  Required format: <type>/KIJ-<number>-<description>"
  echo "  Allowed types: feature, fix, hotfix, improvement, release, prd, research"
  exit 1
fi
exit 0
```

Setup: `git config core.hooksPath .githooks`
