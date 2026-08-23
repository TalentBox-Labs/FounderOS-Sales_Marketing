# S3.5 — Known Exception Reconciliation

**Previous state (S3 report):** CHANGED  
**S3.5 verdict:** RECONCILED

## What changed (exact)

### S3 supersession of S2.5 freeze-test assertion (1)

| Prior assertion (S2.5 at freeze) | S3 update | Reason |
|----------------------------------|-----------|--------|
| `test_freeze_crm_api_residual_documented` expected `optional_tenant_mutation` **not** in `crm_mod` | Same test now expects guards **present** + S3 register shows MITIGATED | S3 legitimately closed risk #9 |

**Test ID unchanged:** `tests/test_saas_s2_5_tenant_isolation_baseline_freeze.py::test_freeze_crm_api_residual_documented`

**S2.5 documentation:** Remains immutable v1.0 historical snapshot (`S2_5_RESIDUAL_TENANCY_RISK_REGISTER_v1.0.md` still lists CRM as S3_REQUIRED / DEFERRED_TO_S3).

### Historical failures (unchanged)

| Category | Count | Identity match | Reason match |
|----------|-------|----------------|--------------|
| FAILED | 8 | PASS | PASS |
| ERROR | 4 | PASS | PASS |

#### FAILED (8) — identical

1. `tests/test_crews_unit.py::TestQACrew::test_qa_crew_validates_output_format`
2. `tests/test_crews_unit.py::TestEditorCrew::test_editor_crew_validates_output`
3. `tests/test_crews_unit.py::TestEditorCrew::test_editor_crew_rejects_output_without_frontmatter`
4. `tests/test_utilities_unit.py::TestFileOperations::test_read_file_returns_content`
5. `tests/test_utilities_unit.py::TestFileOperations::test_read_file_raises_on_missing_file`
6. `tests/test_utilities_unit.py::TestFileOperations::test_save_file_creates_directories`
7. `tests/test_utilities_unit.py::TestFileOperations::test_save_file_overwrites_existing`
8. `tests/test_utilities_unit.py::TestDataValidation::test_markdown_structure_validation`

#### ERROR (4) — identical

1. `tests/test_orchestration_api.py::test_orchestration_plan_endpoint_returns_strategy`
2. `tests/test_orchestration_api.py::test_orchestration_run_with_mocked_backend_and_audit_persistence`
3. `tests/test_prospecting_ui.py::test_prospecting_plan_endpoint_returns_stage_allocation_and_leads`
4. `tests/test_prospecting_ui.py::test_prospecting_plan_validation_error_for_invalid_score`

### Prior S2 supersessions (still valid, not re-opened)

- S1.5 tenant-absence assertions superseded by S2: 3 (documented in S2.5 reconciliation)

## Reconciliation answers

| # | Question | Answer |
|---|----------|--------|
| 1 | Which tests/exceptions changed? | 1 S2.5 freeze-test assertion (CRM residual) |
| 2 | Why? | S3 mitigated CRM API tenant gap |
| 3 | Test IDs changed? | NO |
| 4 | Expected assertions updated? | YES — additive supersession in existing test |
| 5 | Historical failures removed? | NO |
| 6 | Historical failures masked? | NO |
| 7 | 8 fail + 4 error identical? | YES |
| 8 | S3 altered only legitimate S2.5 supersession? | YES |
| 9 | Frozen historical artifacts immutable? | YES — S2.5 docs untouched |
| 10 | S3 assertions additive? | YES — S3 docs + guards added; history preserved |

## Known Exceptions Expected

- Historical FAILED: 8
- Historical ERROR: 4
- S1.5 superseded (S2): 3
- S2.5 CRM assertion superseded (S3): 1

**Total categories:** 16

## Known Exceptions Verified

- Historical FAILED: 8
- Historical ERROR: 4
- S1.5 superseded: 3 (unchanged)
- S3 CRM supersession: 1 (documented)

**Exception Identity Match:** PASS  
**Exception Failure-Reason Match:** PASS  
**Historical Failure Identity Match:** PASS  
**Historical Failure-Reason Match:** PASS  

**Status:** RECONCILED
