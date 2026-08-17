# E6B — Editorial Readiness Read Model

Sprint E6B — Implementation (read-only, additive)  
Date: 2026-08-09  
Repository: `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`

Evidence: [14_FIRST_IMPLEMENTATION_UNIT.md](14_FIRST_IMPLEMENTATION_UNIT.md), [15_SPRINT_E6A_VERDICT.md](15_SPRINT_E6A_VERDICT.md)

---

# Scope

Implemented **GET-only** Editorial Readiness read model:

- Aggregates existing tracker fields, artifact presence, and QA report files
- Does **not** re-run validators, crews, promote, or publish
- Does **not** invent approval or lifecycle semantics

---

# Files Changed

| File | Reason | Risk | Rollback |
|------|--------|------|----------|
| `runner_api_routers/editorial.py` | New Editorial Engine readiness builder + route | Low | Delete module |
| `runner_api.py` | `include_router(editorial_router)` | Low | Remove import/include |
| `tests/test_editorial_readiness.py` | Focused readiness tests | Low | Delete |
| `docs/migration/editorial-engine/E6B_IMPLEMENTATION.md` | Sprint record | None | Delete |

**Not changed:** Content Studio API contract, prompts, crews, DB, UI templates, CMS imports.

**Ownership choice:** Dedicated `editorial` router (`/api/v1/editorial/...`) rather than extending Content Studio, to keep Editorial Engine boundary clear without duplicating CS inventory routes.

---

# Readiness Model

Response shape (observational):

| Field | Meaning |
|-------|---------|
| `tracker.*` | Exact tracker strings (`status`, `qa_status`, `current_step`, …) |
| `artifacts` | Existing `_week_artifacts` booleans |
| `reports.<validator>` | `{available, path, verdict}` for existing `output/qa_reports/{id}_*.md` |
| `readiness.draft_available` | `artifacts.draft` |
| `readiness.editor_review_available` | `artifacts.final` (05_Final presence) |
| `readiness.qa_available` | draft validation report and/or tracker `qa_status` and/or CrewAI_QA report |
| `readiness.validation_passed` | `true` only if all **default** reports present with `PASS`; `false` if any `FAIL`; else `null` (incomplete) |
| `readiness.metadata_valid` / `structure_valid` | bool or `null` from report verdicts |
| `readiness.final_artifact_available` | `artifacts.final` |
| `readiness.publish_checklist_available` | `artifacts.checklist` |
| `readiness.readiness_summary` | Evidence descriptor only: `all_default_reports_pass` \| `has_failures` \| `incomplete_evidence` |

Verdict values for reports: `PASS` | `FAIL` | `missing` | `malformed` | `missing_verdict` | `unreadable`.

**Not claimed:** publish permission, approval, stage readiness.

---

# Data Sources

```
tracker.csv (via Content Studio build_content_detail)
+ input/{id} artifact presence (_week_artifacts)
+ output/qa_reports/{id}_*.md (existing files only)
→ GET /api/v1/editorial/readiness/{content_id}
```

---

# Validator Reuse

| Signal | Source | Re-executes validator? |
|--------|--------|------------------------|
| research_mapper | `*_Research_Map.md` | No — reads report |
| draft_validator | `*_Draft_Validation.md` | No |
| structure_checker | `*_Structure_Check.md` | No |
| metadata_checker | `*_Metadata_Check.md` | No |
| publish_checklist_checker | `*_Publish_Checklist_Check.md` | No |
| content_quality_checker | optional `*_Content_Quality_Check.md` | No |
| crewai_qa | optional `*_CrewAI_QA.md` | No |

Filename conventions aligned with `runner_api_routers/ui.py` `_validator_results`.  
No duplicated checker logic; Final Verdict parsing improved to avoid false `FAIL` from `## Failed Checks` headers.

---

# API Contract

```
GET /api/v1/editorial/readiness/{content_id}
```

| Status | When |
|--------|------|
| 200 | Tracker content exists; body always observational |
| 404 | Content not in tracker |
| 400 | Malformed content id |

Content Studio routes unchanged:

- `GET /api/v1/content-studio/content`
- `GET /api/v1/content-studio/content/{content_id}`

---

# Read-Only Guarantee

**PASS**

- GET only
- No tracker.csv / input/ / DB writes
- No CrewAI / Celery / publish / sheet_sync invocation
- Focused tests hash FS trees and assert no subprocess/crew calls

---

# Approval ADR Boundary

**PRESERVED**

E6B does not define who can approve, what approval means, whether QA approval is mandatory, or whether readiness permits publishing.  
`readiness_summary` is an evidence label only.

---

# Focused Tests

`tests/test_editorial_readiness.py`: **14/14**

---

# Integration Tests

Related suites (readiness + Content Studio + pipeline/validator units + routers integration): **88/88**

---

# Full Regression

**265 passed / 273 total; 8 failed; 0 errors**

Same 8 historical leave-behinds as E4/E6A baselines. **New regressions: 0** (prior E4A was 251/259; +14 readiness tests).

---

# Runtime Verification

| Case | Result |
|------|--------|
| `GET .../readiness/W01` live | 200; `all_default_reports_pass`; `validation_passed=true` |
| Missing `W00` | 404 Content not found |
| Isolated FAIL structure report | `validation_passed=false`; `has_failures` (no repo mutation) |
| Content Studio list | unchanged 200 |

---

# Deferred Capabilities

Explicitly deferred:

- approval
- workflow mutation
- promotion
- publishing readiness mutation
- editor assignment
- review assignment
- `/edit` / `/generate` staging fix
- CMS ritual port
- UI readiness panel (optional follow-up)
- Calendar

---

# Architecture Impact

**NO ARCHITECTURAL CHANGE**

Additive Editorial Engine read router under existing FastAPI app. Marketing OS → Editorial Engine boundary documented in E6A remains intact.
