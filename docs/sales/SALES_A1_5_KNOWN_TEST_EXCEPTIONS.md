# SALES A1.5 — Known Focused-Test Exceptions

**STATUS: FROZEN (exceptions register)**  
**Sprint:** SALES A1.5  
**Date:** 2026-08-13  
**Source:** [SALES_A1_TEST_CLASSIFICATION.md](SALES_A1_TEST_CLASSIFICATION.md)

**Rule:** Do not alter tests merely to achieve 17/17.

---

## Re-verification (A1.5)

Focused suite:

```text
tests/test_sales_api_runner.py
tests/test_lead_prospecting_service.py
tests/test_prospecting_ui.py
tests/test_r1c_route_hygiene.py
```

**Result: 15 passed, 2 errors** — identities match A1 exactly.

**Known Exceptions: 2**  
**New Regressions: 0**

---

## Exception 1

| Field | Value |
|-------|--------|
| Test | `tests/test_prospecting_ui.py::test_prospecting_plan_endpoint_returns_stage_allocation_and_leads` |
| Root cause | `OperationalError` — PostgreSQL localhost:5432 refused; `TestClient(revenue_os.main.app)` requires DB |
| Classification | **ENVIRONMENT_DEPENDENCY** (primary); secondary **ARCHITECTURAL_CONFLICT** (JWT vs runner dual stack) |
| Historical / new | **HISTORICAL** (in full-regression 4-error set) |
| Architecture-related? | Dual-stack note only — not a Sales domain-model defect |
| Blocking freeze? | **NO** |
| Remediation owner | Eng / Sales test hygiene |
| Future remediation gate | Post-A2: DB fixture for JWT tests **or** migrate assertions to runner client |

---

## Exception 2

| Field | Value |
|-------|--------|
| Test | `tests/test_prospecting_ui.py::test_prospecting_plan_validation_error_for_invalid_score` |
| Root cause | Same PostgreSQL connection refused |
| Classification | **ENVIRONMENT_DEPENDENCY** (primary); secondary **ARCHITECTURAL_CONFLICT** |
| Historical / new | **HISTORICAL** |
| Architecture-related? | Dual-stack note only |
| Blocking freeze? | **NO** |
| Remediation owner | Eng / Sales test hygiene |
| Future remediation gate | Same as Exception 1 |

---

## Freeze gate

If either failure identity changes or a third focused failure appears → **STOP** baseline freeze.

A1.5: identities **UNCHANGED** → freeze allowed.
