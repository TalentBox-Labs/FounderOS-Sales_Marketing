# SALES A3.5 — Known Test Exceptions

**STATUS: FROZEN (register)**  
**Sprint:** SALES A3.5  
**Date:** 2026-08-13

---

## A3 focused suite — no exceptions

| Suite | Result |
|-------|--------|
| `tests/test_a3_runner_deal_stage.py` | **15/15** — freeze requires 100% |

---

## A1.5 focused suite — inherited exceptions (verified)

**Expected: 2** · **Verified: 2** · Identity **MATCH** · Reason **MATCH**

| # | Test | Reason | Class |
|---|------|--------|-------|
| 1 | `tests/test_prospecting_ui.py::test_prospecting_plan_endpoint_returns_stage_allocation_and_leads` | PostgreSQL connection refused (`OperationalError`) | ENVIRONMENT_DEPENDENCY |
| 2 | `tests/test_prospecting_ui.py::test_prospecting_plan_validation_error_for_invalid_score` | Same | ENVIRONMENT_DEPENDENCY |

Source of truth for exception definitions: `SALES_A1_5_KNOWN_TEST_EXCEPTIONS.md` (not rewritten).  
Reconciliation evidence: `docs/sales/a3_5/A3_5_A1_5_EXCEPTION_RECONCILIATION.md`.

A3 did **not** modify these tests or their failure mode.

---

## Full regression historical failures

Identities **UNCHANGED** (8 failed + 4 errors including the two A1.5 exceptions above).  
**New Regressions: 0**
