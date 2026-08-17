# R1A — Pre-Clean Baseline (SENTINEL)

**Date:** 2026-08-12  
**Sprint:** R1A  
**Environment:** `SECRET_KEY=test-secret-key HEARTBEAT_ENABLED=0` · `.venv`

---

## Ladder

| Step | Result |
|------|--------|
| compileall `src` / `runner_api_routers` / `revenue_os` | **PASS** |
| `import runner_api` | **PASS** |
| Focused frozen engines (Publishing, Editorial, Website, Deployment, SEO S1/S2) | **104 passed** |
| Full regression | **388 passed; 8 failed; 4 errors** |
| Startup smoke | **PARTIAL** (`/marketing` → 500; others 200) |

---

## Historical failure identities (exact)

### ERRORS (4)

1. `tests/test_orchestration_api.py::test_orchestration_plan_endpoint_returns_strategy`  
2. `tests/test_orchestration_api.py::test_orchestration_run_with_mocked_backend_and_audit_persistence`  
3. `tests/test_prospecting_ui.py::test_prospecting_plan_endpoint_returns_stage_allocation_and_leads`  
4. `tests/test_prospecting_ui.py::test_prospecting_plan_validation_error_for_invalid_score`  

### FAILED (8)

1. `tests/test_crews_unit.py::TestQACrew::test_qa_crew_validates_output_format`  
2. `tests/test_crews_unit.py::TestEditorCrew::test_editor_crew_validates_output`  
3. `tests/test_crews_unit.py::TestEditorCrew::test_editor_crew_rejects_output_without_frontmatter`  
4. `tests/test_utilities_unit.py::TestFileOperations::test_read_file_returns_content`  
5. `tests/test_utilities_unit.py::TestFileOperations::test_read_file_raises_on_missing_file`  
6. `tests/test_utilities_unit.py::TestFileOperations::test_save_file_creates_directories`  
7. `tests/test_utilities_unit.py::TestFileOperations::test_save_file_overwrites_existing`  
8. `tests/test_utilities_unit.py::TestDataValidation::test_markdown_structure_validation`  

**New regressions vs R0:** 0  
**Expected post-clean:** identical identities

---

## Smoke statuses (pre-clean)

| Path | Status |
|------|--------|
| `/`, `/health`, `/content-studio`, `/editorial`, `/publishing`, `/seo`, `/seo/technical`, `/pipeline`, `/sales` | 200 |
| `/marketing` | 500 (`integration_status` undefined) — **pre-existing**, out of R1A scope |
