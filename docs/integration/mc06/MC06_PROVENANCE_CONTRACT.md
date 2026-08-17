# MC06 — Provenance Contract

**Sprint:** FOUNDER OS MC06  
**Date:** 2026-08-13

Accepted CommercialOutcome always retains:

| Field | Meaning |
|-------|---------|
| `deal_id` | Source Deal |
| `source_stage` | Deal.stage at accept (`closed_won`) |
| `value_snapshot` | Deal.value copy |
| `currency_snapshot` | Deal.currency copy |
| `closed_at_snapshot` | Deal.closed_at copy |
| `outcome_id` | Handoff identity |
| `requested_by` | Human actor |

`value_authoritative: false`  
`recognized_revenue: false`

FAILURE H classification: snapshots are **not** financial truth. Authoritative commercial value remains on Revenue `Deal`.
