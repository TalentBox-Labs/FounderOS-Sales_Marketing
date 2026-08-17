# A4.5 — A1.5 Exception Reconciliation (CIPHER)

**Sprint:** SALES A4.5  
**Date:** 2026-08-13  
**Critical freeze gate**

Authoritative register: `docs/sales/SALES_A1_5_KNOWN_TEST_EXCEPTIONS.md`

A1.5 focused suite (unchanged set):

```text
tests/test_sales_api_runner.py
tests/test_lead_prospecting_service.py
tests/test_prospecting_ui.py
tests/test_r1c_route_hygiene.py
```

**Current result (A4.5 re-run): 15 passed, 2 errors**

---

## Mapping

| Historical Exception | Current Test | Historical Failure Type | Current Failure Type | Historical Reason | Current Reason | Identity | Reason |
|---------------------|--------------|-------------------------|----------------------|-------------------|----------------|----------|--------|
| Exception 1 | `tests/test_prospecting_ui.py::test_prospecting_plan_endpoint_returns_stage_allocation_and_leads` | ERROR | ERROR | `OperationalError` — PostgreSQL localhost:5432 refused | `psycopg2.OperationalError` / `sqlalchemy.exc.OperationalError` — connection refused localhost:5432 | **MATCH** | **MATCH** |
| Exception 2 | `tests/test_prospecting_ui.py::test_prospecting_plan_validation_error_for_invalid_score` | ERROR | ERROR | Same PostgreSQL connection refused | Same ERROR / connection refused (pair with Exception 1) | **MATCH** | **MATCH** |

---

## Gate checks

| Check | Result |
|-------|--------|
| Exactly 2 failures in A1.5 suite | **PASS** |
| Identities = documented exceptions | **PASS** |
| Failure reason unchanged (ENVIRONMENT_DEPENDENCY / DB refused) | **PASS** |
| No additional A1.5 frozen test fails | **PASS** |
| No previously passing A1.5 test newly failing | **PASS** (15 pass retained) |
| A4 altered these exception tests? | **NO** — `test_prospecting_ui.py` not part of A4 change set |

**A1.5 Expected Exceptions: 2**  
**A1.5 Exceptions Verified: 2/2**  
**Exception Identity Match: PASS**  
**Exception Failure-Reason Match: PASS**

Freeze may proceed.
