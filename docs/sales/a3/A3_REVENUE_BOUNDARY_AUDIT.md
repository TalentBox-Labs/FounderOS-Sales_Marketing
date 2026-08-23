# A3 — Revenue Boundary Audit (LEDGER)

**Sprint:** SALES A3  
**Date:** 2026-08-13  
**Contract:** `SALES_REVENUE_BOUNDARY_CONTRACT_v1.0` FROZEN

## closed_won behavior

| Action | Owner | A3 behavior |
|--------|-------|-------------|
| Set `Deal.stage = closed_won` | Sales ops on Revenue SoT | VIA `advance_deal_stage` |
| Set `Deal.closed_at` | Existing `advance_deal_stage` | YES — existing field write |
| Create `CommercialOutcome` event object | Future contract | **NO** — not implemented; must not invent |
| Create Client/Project | Revenue/CS future | **NO** |
| Auto Contact.status → CUSTOMER | Future | **NO** |
| n8n `deal_stage_changed_webhook` | JWT path only | **NO** on runner A3 path |

## Verdict

Stage mutation including `closed_won` **preserves** Sales↔Revenue contract: updates Deal fields only; does **not** expand Sales into revenue recognition or CommercialOutcome.

**Sales ↔ Revenue Contract: UNCHANGED**
