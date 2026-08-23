# MC06 — Implementation Decision

**Sprint:** FOUNDER OS MC06  
**Date:** 2026-08-13  
**Gate:** PASS

| Field | Value |
|-------|-------|
| Implementation Type | **BUILD_NEW** (CONNECT_EXISTING persistence/authority) |
| Closed-won coupling | **A — explicit human handoff after closed_won** |
| Canonical Deal SoT | Reused read-only |
| CommercialOutcome model | NONE_FOUND — `AgentActionLog` representation |
| Database migration | **0** |
| UI / cockpit | **0** |

## Why not couple to A3.5 stage PATCH

A3.5 frozen contract hard-codes `commercial_outcome_emitted: false`. Auto-emit on stage change would:

- Change A3.5 frozen behavior
- Silently create Revenue representation without a distinct Revenue accept
- Fail FAILURE A (closed_won silently creates Revenue state)

## Files

| File | Change |
|------|--------|
| `revenue_os/services/commercial_outcome_service.py` | New |
| `runner_api_routers/commercial_outcome.py` | New |
| `runner_api.py` | Router register |
| `revenue_os/automation/events.py` | Three EventType values |
| `tests/test_mc06_commercial_outcome.py` | New |
| `docs/integration/mc06/*` | New |

## Unchanged (frozen)

- `deal_automation_service.py` / `crm.py` stage path
- `lead_scoring_service.py` Contact.status
- `qualified_demand_service.py`
- A1.5 / A3.5 / A4.5 / MC04.5 / UI2.5 docs
