# S4.5 — Known Exception Reconciliation

**S4 report:** Known Exceptions UNCHANGED  
**S4.5 verdict:** RECONCILED / UNCHANGED

## Historical envelope

| Category | Count | Identity match | Reason match |
|----------|-------|----------------|--------------|
| FAILED | 8 | PASS | PASS |
| ERROR | 4 | PASS | PASS |

### FAILED (8)

1. `tests/test_crews_unit.py::TestQACrew::test_qa_crew_validates_output_format`
2. `tests/test_crews_unit.py::TestEditorCrew::test_editor_crew_validates_output`
3. `tests/test_crews_unit.py::TestEditorCrew::test_editor_crew_rejects_output_without_frontmatter`
4. `tests/test_utilities_unit.py::TestFileOperations::test_read_file_returns_content`
5. `tests/test_utilities_unit.py::TestFileOperations::test_read_file_raises_on_missing_file`
6. `tests/test_utilities_unit.py::TestFileOperations::test_save_file_creates_directories`
7. `tests/test_utilities_unit.py::TestFileOperations::test_save_file_overwrites_existing`
8. `tests/test_utilities_unit.py::TestDataValidation::test_markdown_structure_validation`

### ERROR (4)

1. `tests/test_orchestration_api.py::test_orchestration_plan_endpoint_returns_strategy`
2. `tests/test_orchestration_api.py::test_orchestration_run_with_mocked_backend_and_audit_persistence`
3. `tests/test_prospecting_ui.py::test_prospecting_plan_endpoint_returns_stage_allocation_and_leads`
4. `tests/test_prospecting_ui.py::test_prospecting_plan_validation_error_for_invalid_score`

## S4.5 changes

- No historical tests removed or masked
- Additive freeze tests only

**Known Exceptions Expected:** 12 (8 fail + 4 error)  
**Known Exceptions Verified:** 12  
**Status:** UNCHANGED
