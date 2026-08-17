# UI2.5 — Known Test Exceptions

**STATUS: FROZEN (register)**  
**Date:** 2026-08-13

---

## UI2.5 / UI2 / UI1.1 focused suites

| Suite | Expected | Verified |
|-------|----------|----------|
| `tests/test_ui2_5_cockpit_baseline_freeze.py` | 20/20 | 20/20 |
| `tests/test_ui2_executive_cockpit.py` | 23/23 | 23/23 |
| `tests/test_ui1_1_mutation_authority.py` | 10/10 | 10/10 |
| `tests/test_mc04_qualified_demand.py` | 12/12 | 12/12 |
| `tests/test_a4_runner_contact_status.py` | 15/15 | 15/15 |
| `tests/test_a3_runner_deal_stage.py` | 15/15 | 15/15 |

## A1.5 inherited exceptions (2)

| # | Test | Reason | Class |
|---|------|--------|-------|
| 1 | `tests/test_prospecting_ui.py::test_prospecting_plan_endpoint_returns_stage_allocation_and_leads` | PostgreSQL connection refused (`OperationalError`) | ENVIRONMENT_DEPENDENCY |
| 2 | `tests/test_prospecting_ui.py::test_prospecting_plan_validation_error_for_invalid_score` | Same | ENVIRONMENT_DEPENDENCY |

**Identity:** MATCH (unchanged from A1.5 / MC04.5 / UI2 baselines)  
**Reason:** MATCH

## Full regression historical failures (8)

| # | Test |
|---|------|
| 1 | `tests/test_crews_unit.py::TestEditorCrew::test_editor_crew_rejects_output_without_frontmatter` |
| 2 | `tests/test_crews_unit.py::TestEditorCrew::test_editor_crew_validates_output` |
| 3 | `tests/test_crews_unit.py::TestQACrew::test_qa_crew_validates_output_format` |
| 4 | `tests/test_utilities_unit.py::TestFileOperations::test_read_file_raises_on_missing_file` |
| 5 | `tests/test_utilities_unit.py::TestFileOperations::test_read_file_returns_content` |
| 6 | `tests/test_utilities_unit.py::TestFileOperations::test_save_file_creates_directories` |
| 7 | `tests/test_utilities_unit.py::TestFileOperations::test_save_file_overwrites_existing` |
| 8 | `tests/test_utilities_unit.py::TestDataValidation::test_markdown_structure_validation` |

## Full regression historical errors (4)

| # | Test |
|---|------|
| 1 | `tests/test_orchestration_api.py::test_orchestration_plan_endpoint_returns_strategy` |
| 2 | `tests/test_orchestration_api.py::test_orchestration_run_with_mocked_backend_and_audit_persistence` |
| 3 | `tests/test_prospecting_ui.py::test_prospecting_plan_endpoint_returns_stage_allocation_and_leads` |
| 4 | `tests/test_prospecting_ui.py::test_prospecting_plan_validation_error_for_invalid_score` |

## Baseline comparison (UI2.5 verification)

| Metric | UI2 entry | UI2.5 verified |
|--------|-----------|----------------|
| Passed | 471 | 491 (+20 UI2.5 freeze tests) |
| Failed | 8 | 8 |
| Errors | 4 | 4 |
| New regressions | 0 | 0 |

**Exception identity match:** PASS  
**Exception failure-reason match:** PASS
