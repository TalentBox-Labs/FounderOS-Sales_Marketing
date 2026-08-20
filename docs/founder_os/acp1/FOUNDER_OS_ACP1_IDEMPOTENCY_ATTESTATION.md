# Founder OS ACP-1 — Idempotency Attestation

| Autonomous effect | Dedupe / retry basis | Duplicate result |
|-------------------|----------------------|------------------|
| Lead score | Contact leaves unscored set after score ≠ 0 | Second heartbeat scores 0 for same contact |
| Follow-up propose | Existing ApprovalRequest collapse `(action_type, target_id)` + follow-up idempotency keys | Deduplicated pending approval |
| Deal-at-risk flag | Org-scoped emit + AgentActionLog | May re-flag on interval (observational; no CRM mutate) |
| Hermes Deal create | N/A — always blocked | Deterministic blocked provenance |
| Gmail inbound | `EmailActivity.message_id` | Skip already-synced |
| Missing tenant | Deterministic `blocked` + AgentActionLog status=`blocked` | Stable fail-closed |

No global idempotency framework added.
