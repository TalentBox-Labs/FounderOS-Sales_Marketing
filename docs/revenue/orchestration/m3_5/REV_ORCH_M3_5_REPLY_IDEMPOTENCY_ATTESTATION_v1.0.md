# REV-ORCH M3.5 — Reply Idempotency Attestation v1.0

## Status: FROZEN

## Deduplication Mechanism

### Primary Key
`EmailActivity.message_id` — sourced from:
1. `payload["message_id"]` (explicit provider message ID)
2. `payload["provider_message_id"]` (alternative field)
3. Fallback: `rev-orch-m3:{sha256(contact_id:body)[:32]}`

### Lookup
`_existing_reply_activity(db, contact_id, message_id)` queries all EmailActivity rows
with matching message_id, then filters by `activity.contact_id == contact_id`.

### Tenant Safety

The deduplication namespace is effectively tenant-safe because:
- Explicit message IDs: dedupe lookup checks `contact_id` match, so same provider message_id
  across different tenants (different contacts) will NOT collide.
- Fallback SHA: includes `contact_id` (UUID) in the hash input, guaranteeing unique keys
  per contact regardless of message body similarity.

### Orchestration-Level Dedup
`run_inbound_reply_handling()` additionally checks `AgentActionLog` for prior assessment
with matching `message_id` before re-running AI analysis.

## Adversarial Proof

| Scenario | Result |
|----------|--------|
| Same tenant, same message_id | Suppressed (idempotent) |
| Different tenants, same provider message_id | Independently accepted |
| Different tenants, same body, no message_id | Different SHA (different contact_id) |
| Webhook retry | Suppressed at Activity layer |

## Contract

```
REPLY_DEDUPLICATION = FROZEN
DEDUPE_NAMESPACE = TENANT_SAFE (via contact_id scoping)
CROSS_TENANT_DEDUPE_COLLISION = BLOCKED
```
