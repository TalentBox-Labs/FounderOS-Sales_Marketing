# OF1.5 — Known Test Exceptions

**STATUS: FROZEN (register)**  
**Sprint:** FOUNDER OS OF1.5  
**Date:** 2026-08-13

OF1.5 freeze suite and OF1 focused suite: **no exceptions**.

Inherited A1.5 (authoritative: `docs/sales/SALES_A1_5_KNOWN_TEST_EXCEPTIONS.md`):

| # | Test | Class | Reason |
|---|------|-------|--------|
| 1 | `tests/test_prospecting_ui.py::test_prospecting_plan_endpoint_returns_stage_allocation_and_leads` | ENVIRONMENT_DEPENDENCY | PostgreSQL localhost:5432 refused |
| 2 | `tests/test_prospecting_ui.py::test_prospecting_plan_validation_error_for_invalid_score` | ENVIRONMENT_DEPENDENCY | Same |

**Identity match:** PASS  
**Failure-reason match:** PASS (`OperationalError` / connection refused)

## Full-regression historical failures (8) — UNCHANGED

| # | Test | Reason |
|---|------|--------|
| 1 | `tests/test_crews_unit.py::TestEditorCrew::test_editor_crew_rejects_output_without_frontmatter` | `assert any("frontmatter" in e.lower()…)` is False |
| 2 | `tests/test_crews_unit.py::TestEditorCrew::test_editor_crew_validates_output` | `assert is_valid is True` → False |
| 3 | `tests/test_crews_unit.py::TestQACrew::test_qa_crew_validates_output_format` | `assert is_valid is True` → False |
| 4 | `tests/test_utilities_unit.py::TestFileOperations::test_read_file_raises_on_missing_file` | `TypeError: Can't instantiate abstract class BaseCrew` |
| 5 | `tests/test_utilities_unit.py::TestFileOperations::test_read_file_returns_content` | Same `BaseCrew` abstract instantiation |
| 6 | `tests/test_utilities_unit.py::TestFileOperations::test_save_file_creates_directories` | Same `BaseCrew` abstract instantiation |
| 7 | `tests/test_utilities_unit.py::TestFileOperations::test_save_file_overwrites_existing` | Same `BaseCrew` abstract instantiation |
| 8 | `tests/test_utilities_unit.py::TestDataValidation::test_markdown_structure_validation` | `assert is_valid` → False |

## Full-regression historical errors (4) — UNCHANGED

| # | Test | Reason |
|---|------|--------|
| 1 | `tests/test_orchestration_api.py::test_orchestration_plan_endpoint_returns_strategy` | PostgreSQL localhost:5432 refused (setup) |
| 2 | `tests/test_orchestration_api.py::test_orchestration_run_with_mocked_backend_and_audit_persistence` | Same |
| 3 | `tests/test_prospecting_ui.py::test_prospecting_plan_endpoint_returns_stage_allocation_and_leads` | Same (A1.5) |
| 4 | `tests/test_prospecting_ui.py::test_prospecting_plan_validation_error_for_invalid_score` | Same (A1.5) |
