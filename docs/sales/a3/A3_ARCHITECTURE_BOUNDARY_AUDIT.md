# A3 — Architecture Boundary Audit (ATLAS)

**Sprint:** SALES A3  
**Date:** 2026-08-13  
**Baseline:** Sales OS Architecture Baseline v1.0 FROZEN (ADR-005)

---

## May mutate (implementation)

| Area | Allowed |
|------|---------|
| Runner CRM route for deal stage | YES — CONNECT_EXISTING |
| Call `advance_deal_stage` | YES — reuse |
| Canonical `Deal` / `DealStage` | YES — no second model |
| EventBus audit `DEAL_STAGE_CHANGED` | YES — existing event type |
| Human requester gate (reuse FDR-002 pattern) | YES |

## Must NOT mutate

| Area | Forbidden |
|------|-----------|
| A1.5 frozen contract docs | NO edits to meaning |
| Marketing OS / frozen engines | NO |
| CommercialOutcome creation | NO (deferred) |
| CRM SPA mount/refactor | NO |
| DB migrations / new Deal schema | NO |
| External integrations / n8n webhooks on this path | NO |
| Agent-autonomous stage mutation | NO — HUMAN_ONLY |

## Ownership reminder

- **Sales:** pipeline ops (stage movement)  
- **Revenue:** Deal entity SoT  
- Stage mutation = Sales ops on Revenue SoT — not ownership transfer  

**Frozen Contract Impact: NONE** (if implementation follows above)
