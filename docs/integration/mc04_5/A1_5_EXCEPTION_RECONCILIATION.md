# MC04.5 — A1.5 Exception Reconciliation (CIPHER)

**Sprint:** FOUNDER OS MC04.5  
**Date:** 2026-08-13

Authoritative register: `docs/sales/SALES_A1_5_KNOWN_TEST_EXCEPTIONS.md`

Focused suite (unchanged):

```text
tests/test_sales_api_runner.py
tests/test_lead_prospecting_service.py
tests/test_prospecting_ui.py
tests/test_r1c_route_hygiene.py
```

**Current result: 15 passed, 2 errors**

| Exception | Test | Historical reason | Current reason | Identity | Reason |
|-----------|------|-------------------|----------------|----------|--------|
| 1 | `test_prospecting_ui.py::test_prospecting_plan_endpoint_returns_stage_allocation_and_leads` | PostgreSQL localhost:5432 refused | `psycopg2.OperationalError` / `sqlalchemy.exc.OperationalError` connection refused | **MATCH** | **MATCH** |
| 2 | `test_prospecting_ui.py::test_prospecting_plan_validation_error_for_invalid_score` | Same | Same | **MATCH** | **MATCH** |

**A1.5 Expected Known Exceptions: 2**  
**A1.5 Known Exceptions Verified: 2/2**  
**Exception Identity Match: PASS**  
**Exception Failure-Reason Match: PASS**

MC04 did not modify `test_prospecting_ui.py`.
