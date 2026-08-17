# CP3 — Revenue Readiness Audit

**Sprint:** CP3  
**Date:** 2026-08-13

---

## Current Revenue capability inventory

| Area | State | Evidence |
|------|-------|----------|
| CRM SoT (Contact, Deal, Company) | **LIVE** | `revenue_os/models/`; runner CRM APIs |
| Deal stage mutation | **FROZEN** | A3.5; `commercial_outcome_emitted: false` |
| Contact.status mutation | **FROZEN** | A4.5 |
| Client / Project models | **PARTIAL** | `revenue_os/models/project.py` — schema exists; no outcome-driven workflow |
| CommercialOutcome event | **CONTRACT_ONLY** | `docs/sales/SALES_REVENUE_CONTRACT.md` §3 — not implemented |
| Revenue intake actions | **MISSING** | No Customer promotion, no CS handoff automation |
| Billing / invoicing | **NOT_APPLICABLE** | Explicitly out of scope for v1 |
| Revenue UI / cockpit | **PARTIAL** | Cockpit commercial flow shows Revenue **NOT YET ACTIVE** |
| Revenue APIs (social, approvals) | **PARTIAL** | Adjacent modules exist; not outcome-connected |
| Tests for closed-won → outcome | **MISSING** | A3.5 asserts `commercial_outcome_emitted: false` |

---

## Closed-won boundary (current)

```python
# runner_api_routers/crm.py, deal_automation_service.py
"commercial_outcome_emitted": False
```

Stage transition to `CLOSED_WON` is **OPERABLE** but explicitly **does not** emit CommercialOutcome. MC04.5 baseline prohibits CommercialOutcome on QD accept.

---

## MC06 bounded slice (evidence-based feasibility)

Per `SALES_REVENUE_CONTRACT.md` and CP2 A2 sequence:

| v1 scope (bounded) | Feasible |
|--------------------|----------|
| Human-gated `CommercialOutcome` event on CLOSED_WON | YES — mirror MC04 event pattern |
| Idempotency key (`outcome_id`) | YES — contract defined |
| Audit trail (EventBus / AgentActionLog) | YES — existing infra |
| `commercial_outcome_emitted: true` flag in stage response | YES — field already present |
| Revenue intake (Customer/Client auto-create) | DEFER v2 — high scope risk |
| External accounting/billing | OUT OF SCOPE |

**Human gate:** Required — same pattern as A3.5 stage mutation and MC04 accept.

**External integration dependency:** **NONE** for v1 stub.

**Accounting/billing scope risk:** **LOW** if v1 is event + audit only (no invoice/payment).

---

## Downstream bottleneck assessment

Post-MC04.5 + UI2.5:

| Upstream | State |
|----------|-------|
| Demand ingress (manual MC04) | OPERABLE |
| Sales qualification | OPERABLE |
| Deal progression | OPERABLE |
| Closed-won stage | OPERABLE |
| **Outcome emission** | **MISSING** |

When Founder closes deals via A3.5, value stops at CRM stage with no Revenue handoff signal. Cockpit commercial flow panel explicitly surfaces this gap.

---

## CP2 delta

| CP2 | CP3 |
|-----|-----|
| EMERGING_DEPENDENCY | **READY_FOR_PRIORITY** |
| MC04 upstream bottleneck | MC04 **complete** |
| MC06 deferred until stage ops | A3.5 **FROZEN** — sequencing unblocked |

---

## Revenue Priority classification

**READY_FOR_PRIORITY**

Not yet **CRITICAL_BOTTLENECK** because manual deal tracking still works and demand volume may be low for solo Founder ops. Becomes critical as closed-won deals accumulate without outcome trail.

Not **NOT_YET_PRIORITY** — contract, patterns, and upstream operability are sufficient to implement bounded MC06 now.

---

## Recommended bounded implementation (decision reference only)

**MC06 — CommercialOutcome v1:** event emission + audit + `commercial_outcome_emitted` flip on human closed-won; **no** Revenue intake automation, **no** billing, **no** schema migration beyond optional audit log if needed.
