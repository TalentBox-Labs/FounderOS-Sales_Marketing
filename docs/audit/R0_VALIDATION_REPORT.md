# R0 — Validation Report (SENTINEL)

**Date:** 2026-08-11 · **Mode:** AUDIT ONLY — no code fixes  
**Environment:** `SECRET_KEY=test-secret-key HEARTBEAT_ENABLED=0` · `.venv`

---

## Ladder results

| Step | Result | Detail |
|------|--------|--------|
| 1. Import / compile | **PASS** | `compileall` OK on `src`, `runner_api_routers`, `revenue_os`; `import runner_api` OK |
| 2. Focused frozen engines | **PASS** | Publishing + Editorial + Website + Deployment + SEO S1/S2: **104 passed** |
| 3. Website/Publishing/Editorial | included in (2) | PASS |
| 4. SEO S1/S2 | included in (2) | PASS |
| 5. Deployment tests | `tests/test_website_deployment.py` | PASS (in 104) |
| 6. UI/API smoke | **PARTIAL** | See startup |
| 7. Full regression | **388 passed; 8 failed; 4 errors** | Identities below |
| 8. Startup smoke | **PARTIAL** | App loads; `/marketing` → **500** |
| 9. Route inventory | **58** routes on `app` | Sample HTML routes mostly 200 |

---

## Full regression identities

### ERRORS (4) — historical

1. `tests/test_orchestration_api.py::test_orchestration_plan_endpoint_returns_strategy`  
2. `tests/test_orchestration_api.py::test_orchestration_run_with_mocked_backend_and_audit_persistence`  
3. `tests/test_prospecting_ui.py::test_prospecting_plan_endpoint_returns_stage_allocation_and_leads`  
4. `tests/test_prospecting_ui.py::test_prospecting_plan_validation_error_for_invalid_score`  

### FAILED (8) — historical

1. `tests/test_crews_unit.py::TestQACrew::test_qa_crew_validates_output_format`  
2. `tests/test_crews_unit.py::TestEditorCrew::test_editor_crew_validates_output`  
3. `tests/test_crews_unit.py::TestEditorCrew::test_editor_crew_rejects_output_without_frontmatter`  
4. `tests/test_utilities_unit.py::TestFileOperations::test_read_file_returns_content`  
5. `tests/test_utilities_unit.py::TestFileOperations::test_read_file_raises_on_missing_file`  
6. `tests/test_utilities_unit.py::TestFileOperations::test_save_file_creates_directories`  
7. `tests/test_utilities_unit.py::TestFileOperations::test_save_file_overwrites_existing`  
8. `tests/test_utilities_unit.py::TestDataValidation::test_markdown_structure_validation`  

**New regressions vs known Social S0 / SEO baseline identities:** **0**

---

## Startup smoke (TestClient)

| Path | Status |
|------|--------|
| `/`, `/health`, `/content-studio`, `/editorial`, `/publishing`, `/seo`, `/seo/technical`, `/pipeline`, `/sales`, `/analytics`, `/mcp`, `/weeks` | **200** |
| `/marketing` | **500** — `jinja2.UndefinedError: 'integration_status' is undefined` (`templates/marketing.html`) |

**Runtime:** PARTIAL  
**Broken routes (runtime):** 1 HTML page (`/marketing`) + 5 in-page dead targets (see UI audit)

---

## Warnings

- Starlette TestClient / httpx deprecation  
- FastAPI `@app.on_event` deprecation  
- CrewAI `reasoning` DeprecationWarning  

---

## Import errors

None on primary `runner_api` import path.

---

## Verdict

Frozen Marketing OS engines validate green. Full suite retains **historical** 8 fail + 4 error set. Live shell mostly healthy; **marketing page template context bug** is a real runtime defect (record only — no fix in R0).
