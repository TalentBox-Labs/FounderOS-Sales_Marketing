# CP4 — Value Chain Map

**Sprint:** CP4 — Founder OS Value-Chain & Product Maturity Priority Review  
**Date:** 2026-08-13  
**Mode:** Read-only decision  
**Post:** MC06.5 CommercialOutcome Baseline v1.0 FROZEN

---

## Repository-supported chain

```
Audience → Demand → QualifiedDemand → Lead/Contact → Company → Deal
    → Closed Won → CommercialOutcome → Revenue → Cash/Recognition
```

| Edge | Class | Evidence |
|------|-------|----------|
| Audience → Demand | **MISSING** | No web form, no inbound handler, no UTM/referrer capture. `WEB_FORM` is enum + QD source map only. Website engine has no `<form>`. |
| Demand → QualifiedDemand | **PARTIAL** | Operator can `POST /api/v1/marketing/qualified-demand/handoff`. No audience-originated creation. No UI. |
| QualifiedDemand → Lead/Contact | **CONNECTED** | MC04.5 accept creates/merges Contact. Cockpit exposes accept. Reject is API-only. |
| Lead/Contact → Company | **PARTIAL** | Optional `company_hint` on accept; JWT `/api/v1/companies` exists; **no runner Company API**, no Jinja UI. |
| Company → Deal | **PARTIAL** | Deal may have `company_id`; create is runner API / unmounted SPA. No operator Company context. |
| Deal → Closed Won | **PARTIAL** | A3.5 `PATCH .../deals/{id}/stage` OPERABLE + human-gated. **No operator UI.** SPA DealDetail is read-only. |
| Closed Won → CommercialOutcome | **PARTIAL** | MC06.5 APIs OPERABLE. **No UI.** A3.5 still `commercial_outcome_emitted: false`. |
| CommercialOutcome → Revenue | **PARTIAL** | Revenue accept/reject records `AgentActionLog` representation only. No intake/Customer/Client. No UI. |
| Revenue → Cash/Recognition | **NOT_IN_SCOPE** | MC06.5 negative scope: billing/recognition excluded. |

---

## CP3 delta

| Item | CP3 | CP4 |
|------|-----|-----|
| Closed-Won → CommercialOutcome | CONTRACT_ONLY | **API CONNECTED** (MC06.5); operator **PARTIAL** |
| First material break | Audience → Demand | **Unchanged** |
| Highest-cost bottleneck | Closed-Won → CommercialOutcome | **Deal → Closed-Won (operator-unexposed)** — backend exists; Founder cannot run it |

---

## Findings

| Finding | Edge |
|---------|------|
| **First material break** | **Audience → Demand** |
| **Highest-cost break** | **Deal → Closed-Won (operator-unexposed)** |

Audience→Demand still blocks automated commercial origin. After MC06.5 the expensive constraint is no longer missing CommercialOutcome code — it is that Deal stage, CO handoff, and Revenue accept are **API-only**, so the frozen chain cannot be operated as a product.
