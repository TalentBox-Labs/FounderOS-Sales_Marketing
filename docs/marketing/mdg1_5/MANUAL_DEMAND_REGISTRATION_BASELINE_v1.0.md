# FOUNDER OS MANUAL DEMAND REGISTRATION BASELINE v1.0

**STATUS: FROZEN**  
**Date:** 2026-08-13  
**Implementation sprint:** FOUNDER OS MDG1  
**Freeze sprint:** FOUNDER OS MDG1.5  
**Implementation type:** CONNECT_EXISTING

**Parents (UNCHANGED):**
- MC04.5 QualifiedDemand Handoff v1.0
- OF1.5 Operator Flow v1.0
- UI2.5 Executive Cockpit v1.0
- UI1.1 mutation authority
- Sales A1.5 / A3.5 / A4.5
- MC06.5 CommercialOutcome v1.0

---

## Semantic freeze (critical)

| Scope | Status |
|-------|--------|
| **Manual Audience → Demand entry** | **OPERABLE** |
| **Public / anonymous Audience → Demand capture** | **NOT IMPLEMENTED** |
| **Total upstream demand-generation capability** | **PARTIAL** |

`MANUAL_OPERABLE` ≠ automated/public Audience → Demand complete.

---

## Frozen operating path

```
Trusted Founder/operator
→ GET /operator/demand/register
→ POST /api/v1/mdg/manual-demand/register
→ MC04.5 register_marketing_handoff (AgentActionLog)
→ OF1.5 Operator accept/reject → Contact → Deal → Closed-Won → CommercialOutcome → Revenue Decision
```

## Implementation evidence map

| Layer | Path | Role |
|-------|------|------|
| UI | `templates/operator_demand_register.html` | Jinja form (extends `base.html`) |
| Page | `runner_api_routers/ui.py` `page_manual_demand_register` | GET route |
| Proxy | `runner_api_routers/manual_demand.py` | Trusted POST adapter |
| Mount | `runner_api.py` `manual_demand_router` | Include |
| Domain | `register_marketing_handoff` | Frozen MC04.5 |
| SoT | `AgentActionLog` (`qualified_demand_handoff`) | Handoff audit only |
| Identity | `_trusted_cockpit_operator()` | Server env; never client |

`ManualDemandRegisterBody` is **ephemeral / non-authoritative / non-persistent**.

## Non-claims

- No public form
- No Contact on register
- No Deal / Revenue mutation on register
- No new Demand ORM model
- No OF1.5 operator POST expansion

## Supersession

New ADR + approved sprint required.
