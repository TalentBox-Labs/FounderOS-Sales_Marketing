# MC04 — Idempotency & Audit Model (LEDGER)

**Sprint:** FOUNDER OS MC04  
**Date:** 2026-08-13

## Idempotency keys

| Key | Scope |
|-----|-------|
| `demand_id` (UUID) | Handoff, accept, reject |

## Audit records (`AgentActionLog`)

| action_type | target_id | When |
|-------------|-----------|------|
| `qualified_demand_handoff` | `demand_id` | Marketing register |
| `qualified_demand_accepted` | `demand_id` | Sales accept |
| `qualified_demand_rejected` | `demand_id` | Sales reject |

## Duplicate safety

| Scenario | Result |
|----------|--------|
| Same handoff twice | Second call idempotent |
| Same accept twice | Same `contact_id`, no duplicate Contact |
| Same email, new demand_id | Merge existing Contact |
| Accept retry after success | Idempotent accept record |
| Reject after accept | 422 |

## Provenance

Marketing attribution stored in Contact `notes` JSON snippet on accept/merge — Sales read-only reference; Marketing audit payload unchanged.

**No new DB tables — uses existing `agent_action_log`.**
