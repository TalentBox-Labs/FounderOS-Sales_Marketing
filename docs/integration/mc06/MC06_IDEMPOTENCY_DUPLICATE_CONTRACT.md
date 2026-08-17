# MC06 — Idempotency / Duplicate Contract

**Sprint:** FOUNDER OS MC06  
**Date:** 2026-08-13

| Key | Rule |
|-----|------|
| `outcome_id` | Primary idempotency key (`AgentActionLog.target_id`) |
| Same `outcome_id` retry | Returns `{idempotent: true}` — no second row |
| Same Deal, different `outcome_id` while prior handoff is open | Rejected (duplicate) |
| Same Deal already accepted | Rejected (duplicate CommercialOutcome) |
| Prior handoff rejected | New `outcome_id` allowed |

Accept and reject are independently idempotent on `outcome_id`.

Accept after reject → 422.  
Reject after accept → 422.
