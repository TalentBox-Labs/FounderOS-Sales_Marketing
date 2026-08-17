# REV-ORCH M2 — Idempotency Contract

## Key format

```
rev-orch-m2:{contact_id}:{cadence_step}:{source_activity_id}
```

Stored in `ApprovalRequest.payload.idempotency_key` and passed to n8n on approved send.

## Protections

| Scenario | Mechanism |
|----------|-----------|
| Duplicate proposal | Eligibility detects pending M2 ApprovalRequest with same step/source/key |
| Duplicate ApprovalRequest (M1 path) | `request_approval` collapses pending same `(action_type, target_id)` |
| Double approve | M1 pattern: `execution_result.executed` + `handed_to_n8n` guard |
| Scheduler retry | Same idempotency key on re-proposal → blocked at eligibility |
| n8n retry | `idempotency_key` in n8n payload |

## Tests

- `test_m2_duplicate_proposal_collapsed`
- `test_m2_double_approve_idempotent`
