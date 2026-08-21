# Founder OS ACP-3 — Durable Work Identity & Reconciliation

## Durable work identity

```
acp2:{work_kind}:{organization_id|no-org}:{target_id|no-target}:{logical_key|default}
```

- Tenant scope is mandatory in the key when org is known.
- Cross-tenant collision is structurally prevented by org segment.
- Scheduler ticks, retries, and recovery share the same key for the same logical unit.
- `work_id = work:{idempotency_key}` (+ `:aN` for attempt provenance).

## Reconciliation

Source of truth for classification: **latest** orchestration `AgentActionLog` row
per idempotency_key within an organization (bounded scan).

| Latest action / condition | RecoveryClass |
|---------------------------|---------------|
| `acp2_work_succeeded` | SUCCEEDED |
| `acp2_work_exhausted` | EXHAUSTED |
| `acp2_work_cancelled` | CANCELLED |
| `acp2_work_blocked` / Hermes Deal | BLOCKED |
| `acp3_ambiguous_effect` | AMBIGUOUS_EFFECT |
| `acp2_work_running` + domain proves done | SUCCEEDED |
| `acp2_work_running` + external/unprovable | AMBIGUOUS_EFFECT |
| `acp2_work_running` + replay-safe incomplete | RETRYABLE / EXHAUSTED |
| `acp2_work_waiting` / HUMAN_REQUIRED pending | WAITING_HUMAN |
| `acp2_work_retryable` / failed (AUTONOMOUS) | RETRYABLE / EXHAUSTED |
| `acp2_work_proposed` (AUTONOMOUS) | RETRYABLE |

### Explicit non-inferences

- Does not fabricate success without success log or domain proof.
- Does not infer approval (ApprovalRequest is authoritative when present).
- Does not infer tenant ownership.
- PROHIBITED / HUMAN_REQUIRED never become autonomous executable via reconcile.

## Bounds

- `DEFAULT_RECONCILE_SCAN_LIMIT = 200`
- `DEFAULT_RECOVERY_EXEC_LIMIT = 25`
- Per-scheduler unit discovery limits remain (e.g. 25 unscored contacts).
