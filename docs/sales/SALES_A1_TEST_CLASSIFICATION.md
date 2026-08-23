# SALES A1 — Focused Test Failure Classification

**Sprint:** SALES A1  
**Date:** 2026-08-13  
**Mode:** Classification only — **zero test changes**

A0 baseline: **Focused Tests: 15/17** (2 errors)

---

## Suite re-run (post A1 docs)

Command:

```bash
pytest tests/test_sales_api_runner.py tests/test_lead_prospecting_service.py \
  tests/test_prospecting_ui.py tests/test_r1c_route_hygiene.py -q
```

**Result: 15 passed, 2 errors** — unchanged.

Full regression: **397/409; 8 failed; 4 errors** — historical identities unchanged.  
**New Regressions: 0**

---

## Failure 1

| Field | Value |
|-------|--------|
| Test | `tests/test_prospecting_ui.py::test_prospecting_plan_endpoint_returns_stage_allocation_and_leads` |
| Symptom | ERROR — `sqlalchemy.exc.OperationalError` connection refused to PostgreSQL localhost:5432 |
| Root cause | Test uses `TestClient(revenue_os.main.app)` which hits DB on request via `build_prospecting_plan` |
| **Classification** | **ENVIRONMENT_DEPENDENCY** (primary) |
| Secondary note | **ARCHITECTURAL_CONFLICT** — tests target JWT `revenue_os.main` prospecting route while live operator path is `runner_api_routers/prospecting.py` on primary runner |
| Sales defect? | No — passes when DB available; runner prospecting covered by `test_sales_api_runner.py` |
| A1 action | Document only |

---

## Failure 2

| Field | Value |
|-------|--------|
| Test | `tests/test_prospecting_ui.py::test_prospecting_plan_validation_error_for_invalid_score` |
| Symptom | ERROR — same PostgreSQL connection refused |
| **Classification** | **ENVIRONMENT_DEPENDENCY** (primary) |
| Secondary note | **ARCHITECTURAL_CONFLICT** (dual stack) |
| A1 action | Document only |

---

## Summary

| Test | Classification |
|------|----------------|
| `test_prospecting_plan_endpoint_returns_stage_allocation_and_leads` | ENVIRONMENT_DEPENDENCY (+ architectural dual-stack note) |
| `test_prospecting_plan_validation_error_for_invalid_score` | ENVIRONMENT_DEPENDENCY (+ architectural dual-stack note) |

**Focused Test Failures Classified: 2/2**

Not classified as: CURRENT_SALES_DEFECT, OBSOLETE_TEST (yet), or requiring A1 test edits.

Future sprint may: (a) add DB fixture for JWT stack tests, or (b) migrate tests to runner client — **not A1 scope**.

---

## Historical context

Both errors appear in full regression historical set (4 errors total with orchestration_api errors). **Historical Failures: UNCHANGED**
