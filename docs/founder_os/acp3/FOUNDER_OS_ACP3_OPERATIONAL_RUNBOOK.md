# Founder OS ACP-3 — Operational Oversight Runbook

## Founder questions → where to look

| Question | Source |
|----------|--------|
| Is autonomous execution enabled? | `runtime_gates.acp2_execution_killed` (inverted) / env `ACP2_AUTONOMOUS_EXECUTION_ENABLED` |
| Is heartbeat/scheduler paused? | `runtime_gates.heartbeat_paused` / `HEARTBEAT_ENABLED` |
| Is ACP execution killed? | `runtime_gates.acp2_execution_killed` |
| What is retryable? | oversight `retryable` / reconcile `buckets.retryable` |
| What is exhausted? | `exhausted` |
| Waiting for human approval? | `awaiting_human` / `waiting_human` |
| Blocked / prohibited? | `blocked` / reconcile `prohibited` |
| Ambiguous recovery? | `ambiguous_effect` — **do not replay blindly** |
| Which tenants? | Per-org summaries only; no cross-tenant dump |
| Recently succeeded? | `succeeded_recently` |
| Requires founder action? | `counts.requires_founder_action` |

API/composition: `compose_orchestration_summary` → founder UI `agent_orchestration`.

## Controls

```bash
# Pause new mutating work + recovery execution
export HEARTBEAT_ENABLED=0

# Kill autonomous execution (fail closed)
export ACP2_AUTONOMOUS_EXECUTION_ENABLED=0

# Observational reconcile only (no recovery exec)
export ACP3_RESUME_ENABLED=0

# Safe resume (after fixing root cause): re-enable gates; next
# acp3_reconcile / bounded_resume_pass recovers ≤25 RETRYABLE units/org
export HEARTBEAT_ENABLED=1
export ACP2_AUTONOMOUS_EXECUTION_ENABLED=1
export ACP3_RESUME_ENABLED=1
```

## Ambiguous external effect

1. Do not re-run outbound/booking blindly.
2. Inspect ApprovalRequest / provider / Activity provenance.
3. Human decides replay or mark resolved manually.

## Escalation categories (do not collapse)

approval required · retry exhausted · ambiguous external effect ·
tenant/ownership failure · prohibited effect · orchestration invariant ·
operational/runtime failure
