# M0.5 Agent Audit Contract

**Sprint:** REV-ORCH M0.5  
**Date:** 2026-08-17

---

## Store

**Canonical:** `AgentActionLog` (`revenue_os/models/automation_state.py`).

Do **not** create a parallel AI audit table.

Existing columns:

- `actor`, `action_type`, `target_type`, `target_id`, `status`, `detail` (JSON), `organization_id` (UUID, nullable), `created_at`

`organization_id` already exists — M1 must **populate it**. `to_dict()` currently omits it; M1 may extend serialization without a new model.

---

## Required detail for worker executions (M1+)

| Concern | Where |
|---------|--------|
| organization | `AgentActionLog.organization_id` + detail |
| workflow | `detail.workflow_id`, `detail.execution_id` |
| worker type | `actor` (e.g. `research_worker`) + `action_type` (`worker_research`) |
| target entity | `target_type=contact`, `target_id` |
| model/provider | `detail.model`, `detail.provider` (no API keys) |
| proposal result | `detail.ok`, hash/summary of output — not full PII dump if avoidable |
| timestamp | `created_at` |
| success/failure | `status` |
| approval linkage | `detail.approval_request_id` |
| execution linkage | `detail.execution_result_ref` or follow-up log from executor |

---

## Existing audit points to extend, not replace

| Event | Current | M1 |
|-------|---------|-----|
| `approval_requested` / `approval_approved` | `approvals.py` | Keep; add org_id |
| `n8n_outbound` | `integrations/n8n.py` | Keep; add org_id + idempotency_key |
| `lead_scored` | Heartbeat | Keep; add org_id |
| Worker proposal | Often Activity NOTE only | Add AgentActionLog |

---

## PII / prompt

Do not store full prompts with emails if a hash + input refs suffice. If body is stored, it is already in ApprovalRequest.payload — do not duplicate unbounded.

---

*End of M0.5 Agent Audit Contract*
