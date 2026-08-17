# Sales Runner Deal Stage Contract v1.0

**STATUS: FROZEN**  
**VERSION: v1.0**  
**Sprint:** SALES A3.5  
**Date:** 2026-08-13  
**Implementation:** SALES A3  
**Baseline:** [SALES_RUNNER_DEAL_STAGE_BASELINE_v1.0.md](SALES_RUNNER_DEAL_STAGE_BASELINE_v1.0.md)

Detailed path also recorded at: `docs/sales/a3_5/A3_5_RUNNER_DEAL_STAGE_CONTRACT_v1.0.md`

---

## Interface

| Item | Contract |
|------|----------|
| Method / path | `PATCH /api/v1/crm/deals/{deal_id}/stage` |
| Auth | Bearer `_verify_api_key` (401 if key configured and missing/wrong) |
| Body | `{ "stage": string, "requested_by": string, "notes"?: string }` |
| Human gate | `is_human_approver(requested_by)` → 403 if fail |
| Business logic | `apply_deal_stage_update` → `advance_deal_stage` |
| SoT | `revenue_os.models.deal.Deal` |
| Audit | `EventBus` `DEAL_STAGE_CHANGED` including `requested_by`, `commercial_outcome_emitted: false` |

---

## Success response (normative fields)

```json
{
  "ok": true,
  "changed": true,
  "requested_by": "<human>",
  "old_stage": "<stage>",
  "new_stage": "<stage>",
  "commercial_outcome_emitted": false,
  "deal": { }
}
```

Same-stage: `changed: false`, HTTP 200.

---

## Error semantics

| Code | Meaning |
|------|---------|
| 401 | Unauthenticated |
| 403 | Non-human / forbidden requester |
| 404 | Deal not found |
| 422 | Invalid deal_id, invalid/non-sales stage, terminal reopen |

---

## Explicit non-goals (frozen out of scope)

- CommercialOutcome emission  
- CRM SPA mount  
- n8n / external webhooks on this path  
- Schema migration  
- Agent-autonomous stage changes  

## Change control

Amendments require ADR superseding this contract version. A1.5 documents must not be rewritten to hide history.
