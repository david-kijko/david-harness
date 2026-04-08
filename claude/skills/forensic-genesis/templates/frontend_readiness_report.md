# Frontend Readiness Report: {{PROJECT_NAME}}

**Generated**: {{TIMESTAMP}}
**Analyzed Path**: {{PROJECT_PATH}}
**Forensic Genesis Version**: 1.0.0

---

## Executive Summary

{{EXECUTIVE_SUMMARY}}

---

## Readiness Score

| Category | Score | Weight | Weighted |
|----------|-------|--------|----------|
| Architecture Integrity | {{ARCH_SCORE}}/10 | 20% | {{ARCH_WEIGHTED}} |
| Code Quality | {{QUAL_SCORE}}/10 | 15% | {{QUAL_WEIGHTED}} |
| Security Posture | {{SEC_SCORE}}/10 | 20% | {{SEC_WEIGHTED}} |
| API Readiness | {{API_SCORE}}/10 | 25% | {{API_WEIGHTED}} |
| State Management | {{STATE_SCORE}}/10 | 10% | {{STATE_WEIGHTED}} |
| Test Coverage | {{TEST_SCORE}}/10 | 10% | {{TEST_WEIGHTED}} |
| **TOTAL** | | 100% | **{{TOTAL_SCORE}}/10** |

### Score Interpretation
- **8-10**: Ready for backend integration
- **6-7.9**: Minor cleanup needed (1-2 weeks)
- **4-5.9**: Significant work required (3-6 weeks)
- **<4**: Major refactoring needed (6+ weeks)

---

## Critical Blockers

{{#if CRITICAL_BLOCKERS}}
These MUST be resolved before backend integration:

{{#each CRITICAL_BLOCKERS}}
### {{this.id}}: {{this.title}}

**Severity**: CRITICAL
**Location**: `{{this.location}}`
**Effort**: {{this.effort_estimate}}

**Problem**:
{{this.description}}

**Impact**:
{{this.impact}}

**Resolution**:
{{this.recommendation}}

---
{{/each}}
{{else}}
No critical blockers found.
{{/if}}

---

## API Integration Points

### Current API Calls

| # | Endpoint | Method | Component | Current State | Data Shape |
|---|----------|--------|-----------|---------------|------------|
{{#each API_CALLS}}
| {{@index}} | `{{this.endpoint}}` | {{this.method}} | {{this.component}} | {{this.state}} | {{this.data_shape}} |
{{/each}}

### Mock Data Locations

{{#each MOCK_DATA}}
- `{{this.path}}`: {{this.description}}
{{/each}}

### Required Backend Endpoints

Based on frontend code analysis, the backend must provide:

| Endpoint | Method | Purpose | Request Schema | Response Schema | Priority |
|----------|--------|---------|----------------|-----------------|----------|
{{#each REQUIRED_ENDPOINTS}}
| `{{this.endpoint}}` | {{this.method}} | {{this.purpose}} | [View](#{{this.request_schema_id}}) | [View](#{{this.response_schema_id}}) | {{this.priority}} |
{{/each}}

---

## Inferred Data Contracts

### Request Schemas

{{#each REQUEST_SCHEMAS}}
#### {{this.id}}: {{this.name}}

```json
{{this.schema}}
```

**Used by**: {{this.used_by}}

---
{{/each}}

### Response Schemas

{{#each RESPONSE_SCHEMAS}}
#### {{this.id}}: {{this.name}}

```json
{{this.schema}}
```

**Expected by**: {{this.expected_by}}

---
{{/each}}

---

## State Management Analysis

### Global State Structure

```
{{STATE_TREE}}
```

### State Readiness Checklist

- [{{STATE_STRUCTURED}}] Global state properly structured
- [{{ACTIONS_CONSISTENT}}] Actions/reducers follow conventions
- [{{SIDE_EFFECTS_ISOLATED}}] Side effects isolated (sagas/thunks/etc)
- [{{LOADING_STATES}}] Loading states handled
- [{{ERROR_STATES}}] Error states handled
- [{{CACHE_STRATEGY}}] Cache invalidation strategy defined
- [{{PERSISTENCE}}] State persistence configured (if needed)

### State Issues

{{#each STATE_ISSUES}}
- **{{this.severity}}**: {{this.description}} (`{{this.location}}`)
{{/each}}

---

## Cleanup Required

### Critical (Must Fix Before Backend)

| # | Issue | Location | Effort | Impact |
|---|-------|----------|--------|--------|
{{#each CLEANUP_CRITICAL}}
| {{@index}} | {{this.title}} | `{{this.location}}` | {{this.effort}} | {{this.impact}} |
{{/each}}

**Total Critical Effort**: {{CRITICAL_TOTAL_EFFORT}}

### Important (Should Fix)

| # | Issue | Location | Effort | Impact |
|---|-------|----------|--------|--------|
{{#each CLEANUP_IMPORTANT}}
| {{@index}} | {{this.title}} | `{{this.location}}` | {{this.effort}} | {{this.impact}} |
{{/each}}

**Total Important Effort**: {{IMPORTANT_TOTAL_EFFORT}}

### Nice to Have

| # | Issue | Location | Effort | Impact |
|---|-------|----------|--------|--------|
{{#each CLEANUP_NICE}}
| {{@index}} | {{this.title}} | `{{this.location}}` | {{this.effort}} | {{this.impact}} |
{{/each}}

**Total Nice-to-Have Effort**: {{NICE_TOTAL_EFFORT}}

---

## Orphaned Features

Components and code that appear unused or incomplete:

{{#each ORPHANS}}
### {{this.name}}

**Type**: {{this.type}}
**Location**: `{{this.location}}`
**LOC**: {{this.loc}}
**Last Modified**: {{this.last_modified}}

**Evidence**: {{this.evidence}}

**Recommendation**: {{this.recommendation}}

---
{{/each}}

**Total Orphaned LOC**: {{ORPHAN_TOTAL_LOC}}
**Recommended Action**: {{ORPHAN_RECOMMENDATION}}

---

## Security Findings Relevant to Backend

{{#each SECURITY_BACKEND_RELEVANT}}
### {{this.id}}: {{this.title}}

**Severity**: {{this.severity}}
**Category**: {{this.category}}

**Issue**:
{{this.description}}

**Backend Implication**:
{{this.backend_implication}}

**Mitigation**:
{{this.mitigation}}

---
{{/each}}

---

## Recommended Integration Approach

### Phase 1: Preparation ({{PHASE1_EFFORT}})

{{#each PHASE1_STEPS}}
1. {{this}}
{{/each}}

### Phase 2: API Integration ({{PHASE2_EFFORT}})

{{#each PHASE2_STEPS}}
1. {{this}}
{{/each}}

### Phase 3: Testing & Validation ({{PHASE3_EFFORT}})

{{#each PHASE3_STEPS}}
1. {{this}}
{{/each}}

---

## Recommended Next Steps

| Priority | Action | Owner | Effort | Dependencies |
|----------|--------|-------|--------|--------------|
{{#each NEXT_STEPS}}
| P{{this.priority}} | {{this.action}} | {{this.owner}} | {{this.effort}} | {{this.dependencies}} |
{{/each}}

---

## Appendix: Full Findings References

- [Architecture Analysis](./findings/01_architecture.json)
- [Code Quality Report](./findings/02_code_quality.json)
- [Security Audit](./findings/03_security.json)
- [Orphan Inventory](./findings/04_orphans.json)
- [Frontend Readiness Details](./findings/05_frontend_readiness.json)
- [JTBD Mapping](./findings/06_jtbd.json)

---

**Report generated by Forensic Genesis v1.0.0**
**NotebookLM Notebook**: {{NOTEBOOKLM_ID}}
**Graphiti Group**: {{GRAPHITI_GROUP}}
