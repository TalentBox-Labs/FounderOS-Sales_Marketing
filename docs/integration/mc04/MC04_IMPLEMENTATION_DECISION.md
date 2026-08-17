# MC04 — Implementation Decision

**Sprint:** FOUNDER OS MC04  
**Date:** 2026-08-13  
**Gate:** PASS

| Field | Value |
|-------|-------|
| Implementation Type | **BUILD_NEW** |
| Marketing source | Operator handoff via `POST .../marketing/qualified-demand/handoff` |
| Sales intake target | `accept_qualified_demand` → Revenue `Contact` |
| Canonical model | Revenue `Contact` + optional `Company` |
| Authority | `is_human_approver` on all three endpoints |
| Audit | `AgentActionLog` + EventBus |
| Idempotency | `demand_id` in audit `target_id` |

## Files changed

| File | Change |
|------|--------|
| `revenue_os/services/qualified_demand_service.py` | New |
| `runner_api_routers/qualified_demand.py` | New |
| `runner_api.py` | Router register |
| `tests/test_mc04_qualified_demand.py` | New |

## Prohibited

- A3.5 / A4.5 frozen files (behavior)
- Marketing frozen contracts
- Revenue CommercialOutcome
- DB migrations

## Gate checklist

| Condition | Result |
|-----------|--------|
| Frozen Contract Impact | **NONE** |
| Database Migration | **NO** |
| External Integration | **NO** |
| Paid Tools | **NO** |

**Proceed to implementation.**
