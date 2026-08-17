# FOUNDER OS OPERATOR FLOW BASELINE v1.0

**STATUS: FROZEN**  
**Date:** 2026-08-13  
**Implementation sprint:** FOUNDER OS OF1  
**Freeze sprint:** FOUNDER OS OF1.5

**Parents (UNCHANGED):**
- Sales OS Architecture Baseline v1.0 (A1.5)
- Sales A3.5 Runner Deal Stage Update v1.0
- Sales A4.5 LeadScorer / Contact.status v1.0
- MC04.5 QualifiedDemand Handoff v1.0
- MC06.5 CommercialOutcome v1.0
- UI2.5 Executive Cockpit v1.0
- UI1.1 mutation authority

---

## Frozen route

`GET /operator` — Jinja page `templates/operator.html` extends `templates/base.html`.  
Handler: `runner_api_routers/ui.py` `page_operator`.  
API prefix: `/api/v1/operator` (`runner_api_routers/operator_flow.py`).

No second shell. No React. CRM SPA remains UNMOUNTED.

---

## Frozen bounded workflow

```
QualifiedDemand → Contact → Deal → Closed-Won → CommercialOutcome → Revenue Decision
```

**Bounded operator flow (Demand → Revenue Decision): COMPLETE**  
**Total Founder OS value chain (Audience → Demand → Revenue Decision): PARTIAL**

Audience → Demand is **outside** this baseline.  
“Founder Operating Flow COMPLETE” **must not** be read as end-to-end value-chain complete.

---

## Frozen implementation SoT

| File | Role |
|------|------|
| `runner_api_routers/ui.py` | `GET /operator` |
| `runner_api_routers/operator_flow.py` | Trusted action proxies |
| `revenue_os/services/operator_flow_read_model.py` | Non-persistent read composition |
| `templates/operator.html` | Operator UI |
| `templates/base.html` | Nav link (shell) |
| `runner_api.py` | Router include |

Cockpit remains UI2.5 (two mutations). Deep-link to `/operator` is navigation only.

---

## Frozen authority

Server `FOUNDER_OS_OPERATOR_NAME` via `_trusted_cockpit_operator()`.  
Client `requested_by` is not a field on operator action bodies and is not trusted.

---

## Runtime-change reconciliation (OF1 reporting)

| Term | Repository meaning (Founder OS sprint reports) |
|------|-----------------------------------------------|
| **Feature Code Changes** | Production source files added or modified (not docs/tests) |
| **Runtime Changes** | New process/env/docker/runtime-config requirements |

OF1 Feature Code Changes **7** = new/modified product files.  
OF1 Runtime Changes **0** = no new env var, container, or process model. `GET /operator` is feature code that reuses existing `FOUNDER_OS_OPERATOR_NAME` (UI2). **Not a discrepancy.** Do not rewrite OF1 evidence.

---

## Supersession

New ADR + approved sprint required.
