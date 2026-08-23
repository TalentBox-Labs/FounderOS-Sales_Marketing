# R1F — Code Hygiene Re-Audit (FORGE)

**Sprint:** R1F  
**Date:** 2026-08-13  
**Mode:** MEASUREMENT ONLY — no deletions

---

## Method

Re-scan against R0 candidate classes and R1D disposition. Confirm presence/absence of prior removals. Classify remaining items; do not delete.

---

## Removal Verification (already done prior sprints)

| Item | Status |
|------|--------|
| `src/*.py.old` (5) | **GONE** |
| `revenue_os/pipeline/` | **GONE** |
| `src/openapi_schemas.py` | **GONE** |
| `scripts/bootstrap_remaining_weeks.py` | **GONE** |
| `scripts/sheets_copy_mirror_values.gs` | **GONE** |
| `_render_orchestration_run_detail` | **GONE** |

---

## Classification of Remaining Candidates

| ID | Path / theme | Class | Notes |
|----|--------------|-------|-------|
| D01 | `src/tools/validation_runner.py` | **DEFERRED** | Present; not wired as primary QA path |
| D02 | `src/crew.py` helpers | **DEFERRED** | Present; overlapping crew entry |
| D03 | `src/artifact_crew.py` / phase2a | **DEFERRED** | Present; optional artifact path |
| D04 | Dual Hashnode (`src/tools/hashnode_publish.py` + `HashnodePublisher`) | **ACTIVE** (compat) / **DEFERRED** consolidate | Optional channel still live |
| D05 | Shadowed `@app` HTML handlers in `runner_api.py` | **DEFERRED** | Routers win; handlers retained |
| D06 | Sheets mirror family (`sheet_sync`, `google_sheet_sync`, …) | **ACTIVE** | Compatibility retained (R1E) |
| D07 | workcrew.ai URL emitters | **ACTIVE** branding / **DEFERRED** rename | Founder domain decision |
| D08 | R1A–R1D removed dead set | **DEAD** (removed) | Not remaining |
| D09 | Audit/migration docs | **HISTORICAL** | Evidence, not runtime |
| D10 | `frontend/` without `dist` | **ACTIVE** optional | Explicit 503 contract |

---

## Counts vs R0 / R1D

| Metric | R0 | After R1D/R1E | R1F measured |
|--------|---:|--------------:|-------------:|
| Dead-code candidates reviewed historically | 15 | 15 | — |
| Confirmed dead removed (cumulative) | 0 | 10 | 10 still gone |
| Deferred still present | — | 5 | **5** |
| New high-confidence dead found this re-audit | — | — | **0** |

**Dead Code Remaining (deferred candidates still in tree): 5**

---

## Orphan utilities / placeholders

No new TODO-only modules identified that are safer to delete than R1D’s deferred set. Placeholder risk is concentrated in optional CRM and deferred crew helpers — **UNKNOWN** only where Founder channel SoT is open (Hashnode), not where code is unreferenced.

**Unknown / Needs Verification (code hygiene slice): 2** (true unused status of shadowed handlers if route tests expand; ArtifactCrew call-graph completeness under rare ops paths).

---

## Compare

Hygiene improved by removing confirmed dead files and clarifying route ownership. Remaining items are **intentionally deferred** compatibility or low-ROI ambiguity — not newly discovered rot.
