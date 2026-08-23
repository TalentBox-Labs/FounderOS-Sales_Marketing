# OPERATOR AUDIT / IDEMPOTENCY CONTRACT v1.0

**STATUS: FROZEN**

Delegates to frozen domain contracts:

| Action | Idempotency / duplicate | Audit |
|--------|-------------------------|-------|
| QD accept/reject | `demand_id` (MC04.5) | `AgentActionLog` |
| Contact.status | Same-status noop (A4.5) | EventBus on change |
| Deal stage | A3.5 terminal/reopen reject | A3.5 EventBus; no CO emit |
| Deal create | New Deal row; no CO | `created_by` operator |
| CO handoff/accept/reject | `outcome_id` + one accepted outcome per Deal (MC06.5) | `commercial_outcome_*` |

Refresh/resubmit of the same `outcome_id` / `demand_id` returns `{idempotent: true}` without a second authoritative row.
