# SALES A0 — Test Baseline (LEDGER)

**Sprint:** SALES A0  
**Date:** 2026-08-13  
**Mode:** AUDIT ONLY — tests not modified to force PASS

---

## Focused Sales-related suite

Files:

- `tests/test_sales_api_runner.py`
- `tests/test_lead_prospecting_service.py`
- `tests/test_prospecting_ui.py`
- `tests/test_r1c_route_hygiene.py` (includes `/app` 503 contract)

| Result | Count |
|--------|------:|
| Collected | 17 |
| Passed | 15 |
| Errors | 2 |
| Failed | 0 |

**Focused Tests: 15/17**

### Historical Sales-adjacent errors (unchanged identities)

```
ERROR tests/test_prospecting_ui.py::test_prospecting_plan_endpoint_returns_stage_allocation_and_leads
ERROR tests/test_prospecting_ui.py::test_prospecting_plan_validation_error_for_invalid_score
```

These match the known repository historical set (also present in full regression). **Not new.**

---

## Full regression

**397 passed / 409 total; 8 failed; 4 errors**

Historical failures (Marketing/utils/orchestration — not introduced by Sales A0):

- 3 × `test_crews_unit` (Editor/QA)
- 5 × `test_utilities_unit`
- 2 × `test_orchestration_api` ERROR
- 2 × `test_prospecting_ui` ERROR

**New Regressions: 0**

---

## Coverage gaps (evidence)

| Area | Gap |
|------|-----|
| Runner `/api/v1/crm/*` CRUD | No dedicated CRM integration suite |
| Deal stage transitions | Under-tested on runner path |
| Companies API | JWT-only; thin Sales test coverage |
| React SPA | No frontend unit/e2e suite observed |

---

## Runtime smoke note

Without local Postgres, CRM GETs return 500 (connection refused). That is **environment**, not a classification of the router as DEAD. Jinja `/sales` returned 200; `/app` returned 503 as designed.
