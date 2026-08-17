# M1.1 Regression Reconciliation

**Sprint:** REV-ORCH M1.1  
**Date:** 2026-08-17  
**Command:** `SECRET_KEY=… DATABASE_URL=sqlite:///… HEARTBEAT_ENABLED=0 RUNNER_API_KEY= pytest tests/ -q`

---

## Previous Historical Envelope (established baseline)

**Source:** `docs/audit/R0_VALIDATION_REPORT.md`, repeated through MC04.5/A4.5 attestations  
**Totals:** varies by era (388–439 passed subset); invariant **8 failed + 4 errors**

### PREVIOUS HISTORICAL FAILURES (8)

| # | Test ID | Reason |
|---|---------|--------|
| 1 | `tests/test_crews_unit.py::TestQACrew::test_qa_crew_validates_output_format` | Fixture omits `## Passed Checks`; validator requires section |
| 2 | `tests/test_crews_unit.py::TestEditorCrew::test_editor_crew_validates_output` | Fixture markdown too short; `Edited content is too short` |
| 3 | `tests/test_crews_unit.py::TestEditorCrew::test_editor_crew_rejects_output_without_frontmatter` | Short content + assertion expects `"frontmatter"` not in `"front matter"` |
| 4 | `tests/test_utilities_unit.py::TestFileOperations::test_read_file_returns_content` | `TypeError`: abstract `BaseCrew` instantiation |
| 5 | `tests/test_utilities_unit.py::TestFileOperations::test_read_file_raises_on_missing_file` | Same abstract `BaseCrew` |
| 6 | `tests/test_utilities_unit.py::TestFileOperations::test_save_file_creates_directories` | Same abstract `BaseCrew` |
| 7 | `tests/test_utilities_unit.py::TestFileOperations::test_save_file_overwrites_existing` | Same abstract `BaseCrew` |
| 8 | `tests/test_utilities_unit.py::TestDataValidation::test_markdown_structure_validation` | `EditorCrew.validate_output` min-length contract |

### PREVIOUS HISTORICAL ERRORS (4)

| # | Test ID | Reason |
|---|---------|--------|
| 1 | `tests/test_orchestration_api.py::test_orchestration_plan_endpoint_returns_strategy` | PostgreSQL connection refused (`OperationalError`) |
| 2 | `tests/test_orchestration_api.py::test_orchestration_run_with_mocked_backend_and_audit_persistence` | Same |
| 3 | `tests/test_prospecting_ui.py::test_prospecting_plan_endpoint_returns_stage_allocation_and_leads` | Same |
| 4 | `tests/test_prospecting_ui.py::test_prospecting_plan_validation_error_for_invalid_score` | Same |

---

## Current Full Regression (post-M1.1)

**Totals:** **896/916 passed; 20 failed; 0 errors**

### CURRENT FAILURES (20)

**Historical core (8) — unchanged:**

Same 8 test IDs as above with same failure reasons.

**Additional cockpit cluster (12):**

| # | Test ID | Reason |
|---|---------|--------|
| 9 | `tests/test_saas_s1_5_identity_foundation_baseline_freeze.py::test_freeze_cockpit_requires_auth` | `TypeError: 'builtin_function_or_method' object is not iterable` at `templates/cockpit.html:53` |
| 10 | `tests/test_saas_s1_identity_foundation.py::test_authenticated_human_opens_cockpit` | Same template bug |
| 11 | `tests/test_ui2_5_cockpit_baseline_freeze.py::test_freeze_cockpit_route_contract` | Same |
| 12 | `tests/test_ui2_5_cockpit_baseline_freeze.py::test_freeze_canonical_jinja_shell` | Same |
| 13 | `tests/test_ui2_5_cockpit_baseline_freeze.py::test_freeze_get_cockpit_no_mutation` | Same |
| 14 | `tests/test_ui2_5_cockpit_baseline_freeze.py::test_freeze_prohibited_mutations_not_in_template` | Same |
| 15 | `tests/test_ui2_executive_cockpit.py::test_cockpit_route_loads` | Same |
| 16 | `tests/test_ui2_executive_cockpit.py::test_cockpit_unauthenticated_follows_open_dev_pattern` | Same |
| 17 | `tests/test_ui2_executive_cockpit.py::test_cockpit_panels_render` | Same |
| 18 | `tests/test_ui2_executive_cockpit.py::test_deferred_actions_not_exposed` | Same |
| 19 | `tests/test_ui2_executive_cockpit.py::test_no_crm_spa_dependency` | Same |
| 20 | `tests/test_ui2_executive_cockpit.py::test_founder_os_shell_branding` | Same |

### CURRENT ERRORS (0)

All 4 historical error tests now **PASS** when `DATABASE_URL=sqlite:///…` is set (standard pytest env).

---

## Classification Matrix

| Item | Classification |
|------|----------------|
| 8 crews/utilities failures | **HISTORICAL_UNCHANGED** |
| 4 orchestration/prospecting errors → pass | **FIXED** (env: sqlite DATABASE_URL vs PostgreSQL refused) |
| 12 cockpit failures | **PRE_EXISTING_NOT_PREVIOUSLY_RUN** (UI2/UI2.5/S1 cockpit tests added in checkpoint `dd2680d`; not in R0 400-test envelope) |
| M1/M1.1 new tests (15) | **TEST_DISCOVERY_CHANGE** (additive; all pass) |
| M1.1 code changes | **No NEW_REGRESSION** in rev-orch/saas-frozen/identity/MC04/MC06 suites |

---

## Forensic Answers

1. **Established 8 failures:** crews_unit ×3 + utilities_unit ×5 (listed above).
2. **Identity identical:** YES for all 8.
3. **Reason identical:** YES for all 8.
4. **Historical 4 errors:** orchestration_api ×2 + prospecting_ui ×2.
5. **Why no longer errors:** Tests pass with sqlite `DATABASE_URL`; errors were PostgreSQL `OperationalError`.
6. **Disposition:** **FIXED** via environment (not M1 code).
7. **Additional 12:** cockpit template bug (`snapshot.panels.attention.data.items` — `data` not iterable).
8. **Present before M1:** YES — cockpit tests exist in branch baseline; outside historical 451-count envelope.
9. **M1 altered discovery:** Added 10 M1 + 5 M1.1 tests only; no removal.
10. **M1 modified cockpit files:** NO.
11. **12 are new regressions from M1:** NO — evidence: M1 diff excludes `templates/cockpit.html`, `runner_api_routers/cockpit.py`.
12. **Comparable invocation:** YES — same `pytest tests/` + env vars; total collected grew from ~451 (MC04.5 era) to 916 (current).

---

## Verdict

**Regression Envelope: FULLY_RECONCILED**  
**New Regressions attributable to M1/M1.1: 0**
