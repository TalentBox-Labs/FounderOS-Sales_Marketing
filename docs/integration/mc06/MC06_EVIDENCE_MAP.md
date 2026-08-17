# MC06 — Repository Evidence Map

**Sprint:** FOUNDER OS MC06 — Commercial Outcome v1  
**Date:** 2026-08-13  
**Mode:** Implementation (bounded)

---

## A. Canonical Deal SoT

| Item | Evidence |
|------|----------|
| Model | `revenue_os/models/deal.py` — `Deal`, `DealStage` |
| Stages | `discovery`, `qualified`, `proposal`, `negotiation`, `closed_won`, `closed_lost` |
| Value / currency | `Deal.value`, `Deal.currency` (Revenue-owned fields) |
| Close timestamp | `Deal.closed_at` set by `advance_deal_stage` on `CLOSED_WON` |

## B. A3.5 closed_won path (FROZEN — not modified)

| Item | Evidence |
|------|----------|
| API | `PATCH /api/v1/crm/deals/{id}/stage` — `runner_api_routers/crm.py` |
| Service | `apply_deal_stage_update` — always `commercial_outcome_emitted: false` |
| Authority | `require_human_mutation_authority` + router `is_human_approver` |
| Terminal | Cannot reopen `closed_won` / `closed_lost` |

## C. Sales → Revenue contract (A1.5 FROZEN)

| Item | Evidence |
|------|----------|
| Binding | `docs/sales/SALES_REVENUE_BOUNDARY_CONTRACT_v1.0.md` |
| Event schema | `docs/sales/SALES_REVENUE_CONTRACT.md` §3 |
| Sales emits | CommercialOutcome at close |
| Revenue records | Outcome representation; intake/billing future |

Frozen A1.5 text remains **NOT_IMPLEMENTED** as a freeze snapshot. MC06 implements the contract **without rewriting** frozen files.

## D. Existing CommercialOutcome runtime

**NONE_FOUND.** No `CommercialOutcome` / `RevenueOutcome` model. Cockpit commercial flow is an honest stub.

## E. Revenue ownership

Revenue owns persisted `Deal` / `Contact` / `Company`. Sales operates `Deal.stage`. Client/Project/BillingRecord exist as unused schema — **not** used by MC06.

## F–G. APIs / runner

No prior CommercialOutcome API. Closest: A3.5 stage PATCH (explicitly non-emitting) and MC04 accept (`commercial_outcome_emitted: false`).

## H. Audit / idempotency precedent

MC04: `AgentActionLog` + `demand_id` as `target_id`. **No new table.** EventBus in-memory only.

## I. Authority

`is_human_approver` + `require_human_mutation_authority`. Forbidden: `ai`, `agent`, `bot`, `automation`, `ai:` / `agent:` prefixes.

## J. MC04 pattern reused

| MC04 | MC06 |
|------|------|
| Marketing handoff → Sales accept/reject | Sales handoff → Revenue accept/reject |
| `AgentActionLog` action types | `commercial_outcome_*` action types |
| `demand_id` idempotency | `outcome_id` idempotency + one-active-handoff per Deal |
| No shared SoT | No shared SoT |
| Human gate both layers | Human gate both layers |

## Implementation choice

**A — explicit human-triggered handoff after closed_won.**

Not B (do not couple A3.5 stage mutation). Coupling would change the frozen A3.5 response contract (`commercial_outcome_emitted: false`).
