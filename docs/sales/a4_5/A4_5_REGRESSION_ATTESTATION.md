# A4.5 — Regression Attestation (LEDGER)

**Sprint:** SALES A4.5  
**Date:** 2026-08-13

---

## Suite results (A4.5 re-run)

| Suite | Expected | Actual | Status |
|-------|----------|--------|--------|
| A4 focused | 15/15 | 15/15 | **PASS** |
| A3.5 frozen | 15/15 | 15/15 | **PASS** |
| A1.5 focused (4 files) | 15/17 | 15/17 | **PASS** |
| Full regression | 427/439; 8 failed; 4 errors | 427/439; 8 failed; 4 errors | **PASS** |

---

## Historical failure identities (unchanged)

**FAILED (8):**
- `tests/test_crews_unit.py::TestQACrew::test_qa_crew_validates_output_format`
- `tests/test_crews_unit.py::TestEditorCrew::test_editor_crew_validates_output`
- `tests/test_crews_unit.py::TestEditorCrew::test_editor_crew_rejects_output_without_frontmatter`
- `tests/test_utilities_unit.py::TestFileOperations::test_read_file_returns_content`
- `tests/test_utilities_unit.py::TestFileOperations::test_read_file_raises_on_missing_file`
- `tests/test_utilities_unit.py::TestFileOperations::test_save_file_creates_directories`
- `tests/test_utilities_unit.py::TestFileOperations::test_save_file_overwrites_existing`
- `tests/test_utilities_unit.py::TestDataValidation::test_markdown_structure_validation`

**ERROR (4):**
- `tests/test_orchestration_api.py::test_orchestration_plan_endpoint_returns_strategy`
- `tests/test_orchestration_api.py::test_orchestration_run_with_mocked_backend_and_audit_persistence`
- `tests/test_prospecting_ui.py::test_prospecting_plan_endpoint_returns_stage_allocation_and_leads`
- `tests/test_prospecting_ui.py::test_prospecting_plan_validation_error_for_invalid_score`

**New Regressions: 0**

---

## A3.5 regression delta

| Metric | A3.5 freeze | A4.5 freeze | Delta |
|--------|-------------|-------------|-------|
| Passed | 412 | 427 | +15 (A4 tests) |
| Failed | 8 | 8 | 0 |
| Errors | 4 | 4 | 0 |

Historical failure identities and reasons: **UNCHANGED**
