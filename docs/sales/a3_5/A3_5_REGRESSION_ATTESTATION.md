# A3.5 — Regression Attestation (NOVA)

**Sprint:** SALES A3.5  
**Date:** 2026-08-13

## Change scope (A3 slice only)

| Category | Count / result |
|----------|----------------|
| Feature expansion beyond A3 | **NONE** |
| Database migration | **NONE** |
| CRM UI change | **NONE** |
| External integration activation | **NONE** |
| Paid tool addition | **NONE** |
| Credential commit | **NONE** |
| Unrelated subsystem modification | **NONE** (Marketing engines untouched) |

## Suites (A3.5 re-run)

| Suite | Result |
|-------|--------|
| A3 focused (`test_a3_runner_deal_stage.py`) | **15/15** |
| A1.5 focused (4 files) | **15/17** (2 known exceptions) |
| Full regression | **412 passed / 424 total**; 8 failed; 4 errors |
| Historical failure identities | **UNCHANGED** |
| New regressions | **0** |

Implementation files in scope: `runner_api_routers/crm.py`, `revenue_os/services/deal_automation_service.py`, `tests/test_a3_runner_deal_stage.py`, `docs/sales/a3/*`.
