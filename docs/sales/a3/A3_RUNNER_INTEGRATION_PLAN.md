# A3 — Runner Integration Plan (HERMES)

**Sprint:** SALES A3  
**Date:** 2026-08-13

```
Runner PATCH /api/v1/crm/deals/{deal_id}/stage
  → _verify_api_key
  → is_human_approver(requested_by)
  → validate sales DealStage
  → load Deal (SessionLocal)
  → apply_deal_stage_update → advance_deal_stage
  → EventBus DEAL_STAGE_CHANGED (+ requested_by)
  → JSON { ok, deal, changed, requested_by }
```

**No** duplicate probability/`closed_at` rules in the router.

**Endpoint:** `PATCH /api/v1/crm/deals/{deal_id}/stage`  
**Body:** `{ "stage": "<sales_stage>", "requested_by": "<human name>", "notes": "" }`
