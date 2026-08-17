# M0.5 Agent Failure Contract

**Sprint:** REV-ORCH M0.5  
**Date:** 2026-08-17  
**Status:** FROZEN semantics for M1+

---

## Default rule

**AI WORKER FAILURE MUST NOT CAUSE BUSINESS MUTATION.**

No silent continue to external execution (n8n send, CRM status, QD/CO accept).

---

| Failure mode | Workflow behavior | Audit | Human/manual |
|--------------|-------------------|-------|--------------|
| Timeout | Fail step; do not file ApprovalRequest; do not send | `status=failed`, reason=timeout | Retry worker from orchestrator |
| Invalid JSON / schema | Fail step; strip nothing into executor | `status=failed`, reason=invalid_schema | Retry or operator draft |
| Hallucinated unsupported evidence | Validator reject (unknown IDs, invented funding) | `status=failed`, reason=evidence_rejected | Retry with enrichment-only facts |
| Empty output | Fail step | `status=failed`, reason=empty | Fallback: skip AI, optional template **only if** still gated by ApprovalRequest |
| Proposes prohibited action (send, mutate stage, pick tenant) | Reject proposal; do not execute proposed action | `status=failed`, reason=policy_denied | Operator |
| Model provider fail | AIService already returns None / template (`ai_service.py`) | `status=failed` or `degraded` | Template draft still requires human approval before send |
| Exceeds retry limit | Terminal fail for that workflow instance | `status=failed`, reason=retry_exhausted | Manual outreach |

---

## Repository alignment

- `AIService._chat` returns `None` on missing key or exception — **no mutation**.
- `sales_agents` return `{"ok": False, "reason": ...}` on missing contact/email — **partial**; still writes nothing privileged except research/follow-up side effects noted in inventory.
- `approvals.decide` only runs executor on approve — worker failure must never reach `decide`.

---

## Prohibited failure behaviors

- Retrying n8n send because the **worker** failed (wrong layer).
- Auto-applying Contact.status because research failed “closed lost.”
- Using CrewAI fallback JSON as if it were authorized send content without ApprovalRequest.

---

*End of M0.5 Agent Failure Contract*
