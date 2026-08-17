# MANUAL DEMAND REGISTRATION ROUTE CONTRACT v1.0

**STATUS: FROZEN**

| Method | Path | Handler |
|--------|------|---------|
| GET | `/operator/demand/register` | `ui.page_manual_demand_register` → `operator_demand_register.html` |
| POST | `/api/v1/mdg/manual-demand/register` | `manual_demand.register_manual_demand` |

## Route invariants

- Canonical Jinja shell (`{% extends "base.html" %}`)
- Non-public / non-anonymous mutation
- API key gate when `RUNNER_API_KEY` set
- Trusted operator env required for POST (`FOUNDER_OS_OPERATOR_NAME`)
- Link from `/operator` (`data-testid="mdg1-register-link"`) is navigation only

## Not frozen

Incidental CSS, copy tone, button labels beyond required testids.

## OF1.5 coexistence

OF1.5 `operator_flow` POST route set remains exactly eight actions.  
MDG registration lives under `/api/v1/mdg/*`, not `/api/v1/operator/actions/*`.
