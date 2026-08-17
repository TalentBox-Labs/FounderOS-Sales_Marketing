# COMMERCIAL OUTCOME IDEMPOTENCY CONTRACT v1.0

**STATUS: FROZEN**  
**Baseline:** Founder OS CommercialOutcome Baseline v1.0  
**Date:** 2026-08-13

---

## Identity

| Key | Role |
|-----|------|
| `outcome_id` (UUID) | Primary idempotency key = `AgentActionLog.target_id` |
| `deal_id` | Source Deal linkage; one **authoritative** accepted outcome per Deal |

---

## Frozen retry / duplicate behavior

| Case | Behavior |
|------|----------|
| Same `outcome_id` handoff retry | `{idempotent: true}` — no second handoff row |
| Same `outcome_id` accept retry | `{idempotent: true}` — no second accepted row |
| Same `outcome_id` reject retry | `{idempotent: true}` — no second reject row |
| Same Deal, different `outcome_id`, prior handoff open | Rejected (duplicate) |
| Same Deal already accepted | Rejected — no second authoritative CommercialOutcome |
| Prior handoff rejected | New `outcome_id` allowed |
| Accept after reject | 422 |
| Reject after accept | 422 |

Repeated equivalent handoffs must not create multiple authoritative (`commercial_outcome_accepted`) records.

Application-level lookup (MC04 pattern). `agent_action_log` has no unique DB constraint — accepted as ACCEPTED_LEGACY, not a new table.
