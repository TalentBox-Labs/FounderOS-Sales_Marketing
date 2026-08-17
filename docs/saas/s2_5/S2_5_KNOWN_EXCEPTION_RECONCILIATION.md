# S2.5 — Known Exception Reconciliation

**S2 reported:** Known Exceptions: CHANGED  
**S2.5 verdict:** RECONCILED

## What changed (exact)

S2 **did not** change the 8 historical FAILED or 4 historical ERROR tests.  
S2 **did** update **3 S1/S1.5 freeze test assertions** that previously enforced "tenant must not exist":

| Prior test (S1.5) | S2 replacement | Reason |
|-------------------|----------------|--------|
| `test_freeze_no_tenant_model_exists` | `test_freeze_s1_5_tenant_boundary_superseded_by_s2` | S2 legitimately added Organization |
| `test_freeze_no_tenant_ids_added` | `test_freeze_s2_tenant_owned_columns_bounded` | S2 added bounded `organization_id` columns |
| `test_no_tenant_domain_scoping_introduced` (S1) | `test_s1_identity_context_remains_non_tenant_s2_extends_separately` | Identity layer stays tenant-free; tenant is separate layer |

Additionally `test_freeze_no_tenant_scoped_queries_added` was narrowed to `test_freeze_no_tenant_scoped_queries_in_identity_layer` — identity routers must not contain org filters (tenant lives in separate modules).

## Historical failure inventory (full test IDs)

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

## Exception identity match

| Category | Expected | Verified | Match |
|----------|----------|----------|-------|
| A1.5 prospecting_ui errors | 2 | 2 | PASS |
| crews_unit failures | 3 | 3 | PASS |
| utilities_unit failures | 5 | 5 | PASS |
| orchestration_api errors | 2 | 2 | PASS |
| S1.5 freeze suite exceptions | 0 | 0 | PASS |

**Exception Identity Match:** PASS

## Failure-reason match

Full regression (post-S2.5): 733 passed, 8 failed, 4 errors — same distribution as S2 report.

| Historical test | Reason (unchanged) |
|-----------------|-------------------|
| crews_unit (3) | QA/editor validation asserts |
| utilities_unit (5) | BaseCrew abstract / markdown validation |
| orchestration_api (2) | PostgreSQL connection refused |
| prospecting_ui (2) | PostgreSQL connection refused |

Tenancy work did **not** mask, rename, or delete these failures.

**Exception Failure-Reason Match:** PASS

## Tests stopped executing?

NO — all historical tests still run in full regression.

## Tenancy masked failures?

NO — postgres-dependent S1 tests fail for same `OperationalError` reason when run without DB; UI/cockpit tests fixed for `organization_id` kwarg in mocks (test-only, not product behavior change).

## Known Exceptions Expected

- Historical FAILED: 8
- Historical ERROR: 4
- S1.5 tenant-absence assertions superseded: 3 (intentional S2 evolution)

## Known Exceptions Verified

- Historical FAILED: 8
- Historical ERROR: 4
- Supersession documented: 3

**Status:** RECONCILED
