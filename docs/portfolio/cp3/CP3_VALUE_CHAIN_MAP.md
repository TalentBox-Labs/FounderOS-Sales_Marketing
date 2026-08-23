# CP3 — Commercial Value Chain Map

**Sprint:** CP3  
**Date:** 2026-08-13  
**Evidence:** Post-MC04.5, post-UI2.5 repository inspection

---

## End-to-end map

```
Content → Publishing → Audience → Demand → QualifiedDemand → Sales Contact
    → Qualification → Deal → Closed-Won → Commercial Outcome → Revenue
```

## Transition classification (current)

| # | Transition | Class | Evidence |
|---|------------|-------|----------|
| 1 | Content → Publishing | **OPERABLE** | Editorial E7 FROZEN; Publishing Engine M1 FROZEN; human promote path |
| 2 | Publishing → Audience | **PARTIAL** | Website static deploy FROZEN; Social LinkedIn adapter `NOT_IMPLEMENTED` (`publishing_engine.py`); FD-01 OPEN |
| 3 | Audience → Demand | **MISSING** | No web-form handler; `WEB_FORM` enum unused by Marketing writer (`SALES_MARKETING_CONTRACT.md`) |
| 4 | Demand → Qualification | **PARTIAL** | Operator can register MC04 handoff; no automated audience→demand capture |
| 5 | Qualification → Sales Contact | **OPERABLE** | MC04.5 FROZEN — handoff/accept/reject + cockpit accept (`qualified_demand_service.py`) |
| 6 | Sales Contact → Qualification (status) | **OPERABLE** | A4.5 human-gated Contact.status FROZEN |
| 7 | Sales Contact → Deal | **PARTIAL** | Runner CRM deal create LIVE; no auto-deal on qualify; CRM SPA unmounted |
| 8 | Deal → Closed-Won | **OPERABLE** | A3.5 human-gated stage FROZEN; `commercial_outcome_emitted: false` |
| 9 | Closed-Won → Commercial Outcome | **CONTRACT_ONLY** | `SALES_REVENUE_CONTRACT.md` defined; MC06 not implemented; no event emission |
| 10 | Commercial Outcome → Revenue | **MISSING** | No Revenue intake; Client/Project models exist but no outcome-driven workflow |

---

## Key findings

| Finding | Transition |
|---------|--------------|
| **First material break (automation origin)** | **Audience → Demand** — no attributable demand capture from audience channels |
| **Primary cross-OS break (post-MC04)** | **Closed-Won → Commercial Outcome** — stage ops proven; outcome event still absent |
| **Highest-cost bottleneck (next fix)** | **Closed-Won → Commercial Outcome** — blocks Revenue path when deals close; MC04 manual path compensates upstream only |
| **Next bottleneck after MC06 stub** | **Commercial Outcome → Revenue intake** (Customer/Client promotion, CS handoff) |

---

## CP2 delta

| Item | CP2 | CP3 |
|------|-----|-----|
| Qualification → Sales Contact | MISSING | **OPERABLE** (MC04.5) |
| First material break | Audience → Demand | **Unchanged** |
| Primary cross-OS priority | MC04 BUILD | **MC06 CommercialOutcome** (MC04 complete) |

---

## Compensating manual paths

| Gap | Workaround |
|-----|------------|
| Audience → Demand | Operator MC04 handoff registration |
| Commercial Outcome | Manual deal close without outcome event; cockpit shows Revenue NOT YET ACTIVE |

Manual paths do not heal automation but keep Founder ops possible.
