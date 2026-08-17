# R1F — Validation Report (SENTINEL)

**Sprint:** R1F  
**Date:** 2026-08-13  
**Mode:** MEASUREMENT ONLY

---

## 1. Compile / Import

| Check | Result |
|-------|--------|
| `compileall` on `src`, `runner_api_routers`, `revenue_os` | **PASS** |
| `import runner_api` | **PASS** |

---

## 2. Application Startup / Route Smoke

TestClient smoke (selected): `/` `/marketing` `/pipeline` `/publishing` `/seo` `/seo/technical` `/health` `/content-studio` `/editorial` → **200**; `/app` → **503** optional.

**Runtime: PASS**

---

## 3–6. Focused Suites

Command set:

- `tests/test_r1c_route_hygiene.py`
- `tests/test_publishing_engine.py`
- `tests/test_editorial_approval.py`
- `tests/test_website_engine.py`
- `tests/test_website_deployment.py`
- `tests/test_seo_readiness_engine.py`
- `tests/test_technical_seo_engine.py`
- `tests/test_site_origin.py`

**Result: 121 passed**

---

## 7. Full Regression

**397 passed / 409 total; 8 failed; 4 errors**

Matches expected post-R1C baseline (397/409).

### Historical failure identities

```
ERROR tests/test_orchestration_api.py::test_orchestration_plan_endpoint_returns_strategy
ERROR tests/test_orchestration_api.py::test_orchestration_run_with_mocked_backend_and_audit_persistence
ERROR tests/test_prospecting_ui.py::test_prospecting_plan_endpoint_returns_stage_allocation_and_leads
ERROR tests/test_prospecting_ui.py::test_prospecting_plan_validation_error_for_invalid_score
FAILED tests/test_crews_unit.py::TestEditorCrew::test_editor_crew_rejects_output_without_frontmatter
FAILED tests/test_crews_unit.py::TestEditorCrew::test_editor_crew_validates_output
FAILED tests/test_crews_unit.py::TestQACrew::test_qa_crew_validates_output_format
FAILED tests/test_utilities_unit.py::TestDataValidation::test_markdown_structure_validation
FAILED tests/test_utilities_unit.py::TestFileOperations::test_read_file_raises_on_missing_file
FAILED tests/test_utilities_unit.py::TestFileOperations::test_read_file_returns_content
FAILED tests/test_utilities_unit.py::TestFileOperations::test_save_file_creates_directories
FAILED tests/test_utilities_unit.py::TestFileOperations::test_save_file_overwrites_existing
```

**Historical Failures: UNCHANGED** (diff vs expected identity set empty)  
**New Regressions: 0**

---

## Scores (test / runtime)

| Score | R0 | Current | Δ |
|-------|---:|--------:|--:|
| Test Health | 78 | **80** | **+2** |
| Runtime Health | 70 | **92** | **+22** |

Test Health: same 12 historical broken identities; focused engines green; R1C hygiene coverage retained.  
Runtime Health: marketing 500 gone; `/app` explicit optional; core shell PASS.
