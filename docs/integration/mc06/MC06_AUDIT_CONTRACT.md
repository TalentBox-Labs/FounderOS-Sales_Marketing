# MC06 — Acceptance / Rejection Audit Contract

**Sprint:** FOUNDER OS MC06  
**Date:** 2026-08-13

## Durable audit

`AgentActionLog` rows with `target_type=commercial_outcome`.

| Event | `action_type` | Extra |
|-------|---------------|-------|
| Handoff | `commercial_outcome_handoff` | payload + provenance |
| Accept | `commercial_outcome_accepted` | deal_id, notes, provenance |
| Reject | `commercial_outcome_rejected` | reason |

## In-memory events (non-durable)

New `EventType` values (do **not** publish `DEAL_CLOSED`, which would trigger finance-adjacent workflows):

- `COMMERCIAL_OUTCOME_HANDED_OFF`
- `COMMERCIAL_OUTCOME_ACCEPTED`
- `COMMERCIAL_OUTCOME_REJECTED`
