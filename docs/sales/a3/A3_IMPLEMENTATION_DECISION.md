# A3 — Implementation Decision (Reconciliation Gate)

**Sprint:** SALES A3  
**Date:** 2026-08-13  
**Gate status:** **PASS — proceed to implementation**

| Gate | Value |
|------|-------|
| Frozen Contract Impact | **NONE** |
| Database Migration | **NO** |
| External Integration Required | **NO** |

---

## Decision summary

| Field | Value |
|-------|--------|
| Existing capability reused | `advance_deal_stage` (+ thin `apply_deal_stage_update` wrapper for sales-stage / terminal rules) |
| Canonical Deal model | YES |
| Runner integration | `PATCH /api/v1/crm/deals/{deal_id}/stage` in `runner_api_routers/crm.py` |
| Authentication | `_verify_api_key` Bearer |
| HUMAN_ONLY | `is_human_approver(requested_by)` → 403 if fail |
| Valid transitions | Sales stages only; same-stage no-op; no reopen from closed_* |
| Sales ↔ Revenue | Update Deal fields only; no CommercialOutcome |
| Audit | EventBus `DEAL_STAGE_CHANGED` with `requested_by` |

## Files expected to change

- `revenue_os/services/deal_automation_service.py` — thin wrapper  
- `runner_api_routers/crm.py` — endpoint  
- `tests/test_a3_runner_deal_stage.py` — new  
- `docs/sales/a3/*` — audit docs  

## Files prohibited

- A1.5 frozen contract markdown (content meaning)  
- Marketing OS engines  
- `frontend/` mount  
- migrations/  
- JWT deals router rewrite (out of scope)  

---

**Proceed to Phase 2.**
