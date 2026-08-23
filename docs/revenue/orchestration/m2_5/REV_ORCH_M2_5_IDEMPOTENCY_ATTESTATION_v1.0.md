# REV-ORCH M2.5 — Idempotency Attestation v1.0

**STATUS: FROZEN**  
**FOLLOWUP_IDEMPOTENCY = FROZEN**

## Key

```
rev-orch-m2:{contact_id}:{cadence_step}:{source_activity_id}
```

Stored in `ApprovalRequest.payload.idempotency_key`; forwarded to n8n on send.

## Protections

| Scenario | Mechanism |
|----------|-----------|
| Repeat scheduler scan | Eligibility sees pending M2 ApprovalRequest → no second proposal |
| Repeat propose API | Eligibility `FOLLOWUP_APPROVAL_PENDING` → 422 |
| Duplicate pending same contact+action | `request_approval` collapse on `(action_type, target_id)` |
| Double approve | `decide` 409 if already decided; executed+handed_to_n8n skip |
| Retry / restart | Same key; pending collapse; execution_result guard |

Tests: `test_m2_5_duplicate_scheduler_scan_does_not_duplicate_proposal`, `test_m2_5_duplicate_approval_does_not_duplicate_send`.
