# Founder OS ACP-2 — Orchestration Contract

**STATUS:** BINDING FOR ACP-2
**Baseline:** `founder-os-acp1-v1.0`

## Rule

ACP-2 is an **orchestration** layer. ACP-1 is the **authority** layer.

```
effective_authority(work) <= ACP1_authority(actor, tenant, effect)
```

Assignment, scheduling, planning, and delegation **never** grant authority.

## Persistence

| Surface | Role |
|---------|------|
| In-memory `WorkItem` | Lifecycle during one orchestration call |
| `AgentActionLog` (append-only) | Provenance events (`acp2_work_*`) — **not** a mutable workflow DB |
| `ApprovalRequest` | Human gate (unchanged) |
| `HeartbeatRun` | Scheduler job run history (unchanged) |
| Env `HEARTBEAT_ENABLED` / `ACP2_AUTONOMOUS_EXECUTION_ENABLED` | Pause / kill future autonomous execution |

**New persistent SoTs: 0. New models: 0. Migrations: 0.**

## Execution modes

| Mode | Meaning |
|------|---------|
| AUTONOMOUS | Execute only after ACP-1 tenant/effect checks pass |
| HUMAN_REQUIRED | Stop before protected effect; use ApprovalRequest |
| PROHIBITED | Never execute (e.g. Hermes Deal create, optional_tenant CRM mutations) |
