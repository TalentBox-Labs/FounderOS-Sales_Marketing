# CommercialOutcome v1 Contract

**Sprint:** FOUNDER OS MC06  
**Date:** 2026-08-13  
**Status:** IMPLEMENTED (bounded)  
**Does not rewrite:** A1.5 / A3.5 / A4.5 / MC04.5 frozen baselines

---

## Purpose

Governed Sales → Revenue handoff representing the commercial consequence of an eligible `closed_won` Deal.

Not recognized revenue. Not a bill. Not a ledger entry.

---

## Eligibility

| Rule | Value |
|------|-------|
| Source entity | Canonical Revenue `Deal` |
| Required stage | `closed_won` only |
| `closed_lost` | Rejected in v1 |
| In-progress stages | Rejected |
| Missing Deal | Rejected |

A3.5 stage mutation remains the only path that writes `Deal.stage`. MC06 **reads** eligibility; it does not close the deal.

---

## APIs

| Method | Path | Owner action |
|--------|------|--------------|
| POST | `/api/v1/sales/commercial-outcome/handoff` | Sales registers handoff |
| POST | `/api/v1/revenue/intake/commercial-outcome/accept` | Revenue accepts representation |
| POST | `/api/v1/revenue/intake/commercial-outcome/reject` | Revenue rejects (audit only) |

---

## Payload (handoff)

Derived from `SALES_REVENUE_CONTRACT.md` §3; unused fields omitted.

| Field | Required | Source |
|-------|----------|--------|
| `outcome_id` | Yes | Caller UUID (idempotency) |
| `deal_id` | Yes | Existing Deal |
| `outcome` | Yes | `closed_won` only |
| `occurred_at` | Yes | ISO timestamp |
| `requested_by` | Yes | Human actor |
| `handoff_hints` | No | Optional note |

Value/currency are **snapshotted from Deal** at handoff/accept. They are provenance, not financial SoT (`value_authoritative: false`).

---

## Persistence

Existing `agent_action_log` rows:

| `action_type` | Meaning |
|---------------|---------|
| `commercial_outcome_handoff` | Sales registered request |
| `commercial_outcome_accepted` | Revenue owns representation |
| `commercial_outcome_rejected` | Revenue rejected request |

No new table. No Deal column. No Client/Project/BillingRecord write.

---

## Ownership

| Phase | Owner | Object |
|-------|-------|--------|
| Before handoff | Sales (ops) | `Deal.stage` via A3.5 |
| After register, before accept | Sales request / Revenue pending | Audit row only |
| After accept | Revenue | CommercialOutcome representation (`AgentActionLog` accepted row) |

Sales never owns the accepted representation. Revenue never writes `Deal.stage` via MC06.
