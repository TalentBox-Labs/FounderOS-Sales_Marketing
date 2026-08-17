# A3.5 — Runner Deal Stage Contract v1.0 (HERMES)

**STATUS: FROZEN** (behavioral)  
**VERSION: v1.0**  
**Sprint:** SALES A3.5

Canonical runtime path:

```
AUTHORIZED HUMAN (requested_by)
        ↓
FOUNDER OS RUNNER  PATCH /api/v1/crm/deals/{deal_id}/stage
  + Bearer API key (_verify_api_key)
        ↓
SALES BOUNDED INTERFACE  (crm.update_deal_stage)
  + is_human_approver
  + sales DealStage validation
        ↓
apply_deal_stage_update → advance_deal_stage
        ↓
CANONICAL Deal SoT (revenue_os.models.deal.Deal)
        ↓
AUDIT: EventBus DEAL_STAGE_CHANGED (requested_by, stages, commercial_outcome_emitted=false)
        ↓
closed_won → Deal fields only
        X  CommercialOutcome / Revenue ownership transfer
```

## Frozen request contract

| Field | Required | Notes |
|-------|----------|-------|
| `stage` | YES | Sales pipeline stage string |
| `requested_by` | YES | Human name; agent identities rejected |
| `notes` | NO | Optional |

## Frozen response / errors

| Outcome | HTTP |
|---------|------|
| Success | 200 `{ ok, changed, requested_by, old_stage, new_stage, commercial_outcome_emitted:false, deal }` |
| Unauthenticated | 401 |
| Non-human requester | 403 |
| Invalid / terminal reopen / bad id | 422 |
| Missing deal | 404 |

## Guarantees (also in baseline)

1. Human authority required  
2. Agent autonomous mutation prohibited  
3. Canonical Deal SoT  
4. No duplicated stage business rules in runner (delegates to `advance_deal_stage`)  
5–6. Valid/invalid transitions enforced  
7. Audit evidence required  
8. closed_won does not transfer Revenue ownership  
9. Sales↔Revenue contract authoritative  
10. CRM UI not required  
11. No external integration required  
12. No DB migration required  
