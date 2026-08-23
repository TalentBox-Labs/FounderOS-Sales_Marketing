# Founder OS ACP-2 — Implementation Plan

## Inventory (repository-grounded)

| Primitive | Path | ACP-2 use |
|-----------|------|-----------|
| ACP-1 boundary | `acp1_autonomous_boundary.py` | Authority / tenant |
| Heartbeat | `scheduler.py` | Producer → orchestrate |
| Hermes | `hermes_planner.py` | Planner; Deal create blocked via orch |
| ApprovalRequest | `approvals.py` | Human escalation |
| AgentActionLog | `activity_log.py` | Append-only provenance |
| Celery tasks | `revenue_os/tasks/` | Dormant; not control plane |

## Persistence audit answer

A. Work identity/status/retry/escalation: **YES** via in-memory WorkItem + append logs + ApprovalRequest
B. Without abusing AgentActionLog as mutable workflow DB: **YES** (append-only events)
C. Restart-safe effects without new SoT: **YES** via deterministic idempotency keys; mid-flight durable pause of individual work items: **CONTRACT_ONLY** (env kill/pause)

## Surfaces

CREATE: `acp2_work_contract.py`, `acp2_effect_catalog.py`, `acp2_orchestration.py`, `acp2_oversight.py`, tests, docs
MODIFY: `scheduler.py` (score/follow-up via orch), `hermes_planner.py` (Deal create via orch), `founder_ui_read_model.py` (summary attach)
