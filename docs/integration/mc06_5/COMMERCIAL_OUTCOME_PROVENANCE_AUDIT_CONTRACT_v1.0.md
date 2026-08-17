# COMMERCIAL OUTCOME PROVENANCE AND AUDIT CONTRACT v1.0

**STATUS: FROZEN**  
**Baseline:** Founder OS CommercialOutcome Baseline v1.0  
**Date:** 2026-08-13

Do not invent new telemetry beyond MC06 fields.

---

## Provenance (minimum)

| Field | Traces |
|-------|--------|
| `deal_id` | Source Deal |
| `source_stage` | Deal.stage at snapshot (`closed_won`) |
| `outcome_id` | Handoff identity |
| `requested_by` / `actor` | Initiating human |
| `occurred_at` | Handoff timestamp (caller) |
| `value_snapshot` / `currency_snapshot` / `closed_at_snapshot` | Deal copies |

`value_authoritative: false`  
`recognized_revenue: false`

Authoritative commercial value remains on Revenue `Deal`. Snapshots are not financial truth.

---

## Durable audit (`AgentActionLog`)

| Event | `action_type` | `target_type` | Extra |
|-------|---------------|---------------|-------|
| Handoff | `commercial_outcome_handoff` | `commercial_outcome` | payload, provenance, requested_by |
| Accept | `commercial_outcome_accepted` | `commercial_outcome` | deal_id, notes, provenance |
| Reject | `commercial_outcome_rejected` | `commercial_outcome` | reason, deal_id |

`target_id` = `outcome_id`.

---

## In-memory events (non-durable)

`COMMERCIAL_OUTCOME_HANDED_OFF` · `COMMERCIAL_OUTCOME_ACCEPTED` · `COMMERCIAL_OUTCOME_REJECTED`

Must **not** publish `DEAL_CLOSED` (would trigger finance-adjacent workflows).
