# Founder OS ACP-2 — Provenance Attestation

Every orchestrated transition appends `AgentActionLog`:

| action_type | When |
|-------------|------|
| `acp2_work_proposed` | Became ELIGIBLE |
| `acp2_work_blocked` | Authority/tenant/prohibited |
| `acp2_work_waiting_human` | HUMAN_REQUIRED |
| `acp2_work_running` | Entered RUNNING |
| `acp2_work_succeeded` | Effect completed / deduped |
| `acp2_work_failed` / `retryable` / `exhausted` | Failure path |
| `acp2_work_delegated` | Parent→child |
| `acp2_work_cancelled` | Kill switch |

Detail includes org, work_id, parent/root, agents, effect, mode, state, idempotency_key.

Hermes Deal blocks also retain ACP-1 `hermes_deal_create_blocked`.
