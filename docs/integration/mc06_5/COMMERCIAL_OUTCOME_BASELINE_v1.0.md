# FOUNDER OS COMMERCIAL OUTCOME BASELINE v1.0

**STATUS: FROZEN**  
**Date:** 2026-08-13  
**Implementation sprint:** FOUNDER OS MC06 (BUILD_NEW)  
**Freeze sprint:** FOUNDER OS MC06.5

**Parents (UNCHANGED):**
- Sales OS Architecture Baseline v1.0 (A1.5)
- Sales A3.5 Runner Deal Stage Update v1.0
- Sales A4.5 LeadScorer / Contact.status v1.0
- Founder OS MC04.5 QualifiedDemand Handoff v1.0
- Sales ↔ Revenue Boundary Contract v1.0 (A1.5) — referenced, not rewritten

---

## Frozen flow

```
eligible Deal.stage = closed_won          (A3.5 — Sales ops; commercial_outcome_emitted: false)
        ↓
human Sales  → POST /api/v1/sales/commercial-outcome/handoff
             → AgentActionLog commercial_outcome_handoff (no Deal write)
        ↓
human Revenue → POST /api/v1/revenue/intake/commercial-outcome/accept|reject
              → AgentActionLog accepted representation OR reject audit
              → no Deal mutation, no billing, no recognition
```

---

## Frozen interfaces

| Method | Path | Authority |
|--------|------|-----------|
| POST | `/api/v1/sales/commercial-outcome/handoff` | Human Sales |
| POST | `/api/v1/revenue/intake/commercial-outcome/accept` | Human Revenue |
| POST | `/api/v1/revenue/intake/commercial-outcome/reject` | Human Revenue |

---

## Frozen implementation SoT

| File | Role |
|------|------|
| `revenue_os/services/commercial_outcome_service.py` | Domain handoff / accept / reject |
| `runner_api_routers/commercial_outcome.py` | Runner API + human gate |
| `runner_api.py` | Router include only |
| `revenue_os/automation/events.py` | `COMMERCIAL_OUTCOME_*` EventType values (in-memory) |

A3.5 files remain the Deal.stage SoT and are **not** part of this baseline's mutation surface.

---

## Frozen persistence

Existing `agent_action_log` (`AgentActionLog`).  
No CommercialOutcome table. No new Revenue model. No migration.

---

## Frozen A3.5 emission invariant

`apply_deal_stage_update` and `PATCH /api/v1/crm/deals/{id}/stage` continue to return:

`commercial_outcome_emitted: false`

MC06 accept may report `commercial_outcome_emitted: true` on the **MC06 accept response only**. That does not change A3.5.

---

## Frozen tests

| File | Role |
|------|------|
| `tests/test_mc06_5_commercial_outcome_baseline_freeze.py` | MC06.5 freeze suite **22/22** |
| `tests/test_mc06_commercial_outcome.py` | MC06 focused **28/28** |

---

## Prohibited without architecture review + new sprint

- Coupling A3.5 stage PATCH to CommercialOutcome emission
- Broadening eligibility beyond `closed_won`
- New CommercialOutcome table / Revenue model / DB migration
- Shared mutable Sales/Revenue SoT
- Billing, invoicing, payments, recognition, tax, subscriptions, ERP, commissions, forecasting
- Deal mutation from MC06 paths
- Agent/AI/spoofed authority
- Cockpit / CRM UI exposure
- Rewriting A1.5 / A3.5 / A4.5 / MC04.5 contracts

---

## Supersession

New ADR + approved sprint required.
