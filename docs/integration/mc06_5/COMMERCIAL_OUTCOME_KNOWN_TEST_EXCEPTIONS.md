# COMMERCIAL OUTCOME KNOWN TEST EXCEPTIONS

**STATUS: FROZEN (register)**  
**Sprint:** FOUNDER OS MC06.5  
**Date:** 2026-08-13

---

## MC06 / MC06.5 focused suites — no exceptions

| Suite | Result at freeze |
|-------|------------------|
| `tests/test_mc06_5_commercial_outcome_baseline_freeze.py` | **22/22** |
| `tests/test_mc06_commercial_outcome.py` | **28/28** |

---

## Inherited A1.5 exceptions (not MC06 defects)

Authoritative register: `docs/sales/SALES_A1_5_KNOWN_TEST_EXCEPTIONS.md` (not rewritten).

| # | Test | Class | Historical |
|---|------|-------|------------|
| 1 | `tests/test_prospecting_ui.py::test_prospecting_plan_endpoint_returns_stage_allocation_and_leads` | ENVIRONMENT_DEPENDENCY | YES |
| 2 | `tests/test_prospecting_ui.py::test_prospecting_plan_validation_error_for_invalid_score` | ENVIRONMENT_DEPENDENCY | YES |

Reconciliation: `MC06_5_A1_5_EXCEPTION_RECONCILIATION.md`.

---

## Full-regression historical set (unchanged identity)

| Kind | Tests |
|------|-------|
| FAILED | `test_crews_unit.py` (3), `test_utilities_unit.py` (5) |
| ERROR | `test_orchestration_api.py` (2), `test_prospecting_ui.py` (2) |

MC06.5 must not change identity or reason of these failures.
