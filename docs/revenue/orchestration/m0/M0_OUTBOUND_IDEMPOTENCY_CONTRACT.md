# M0 Outbound Idempotency Contract

**Sprint:** REV-ORCH M0  
**Date:** 2026-08-17  
**Status:** DEFINED (implementation in M1)

---

## Threat Scenarios

| Scenario | Risk |
|----------|------|
| Approve twice | Double send |
| HTTP retry on approve | Double send |
| n8n retry | Double send |
| Scheduler retry | Double Activity / send |
| API timeout after n8n accepted | Unknown state |

---

## Current Protections

| Mechanism | Location | Coverage |
|-----------|----------|----------|
| Approval dedup | `request_approval()` — pending `(action_type, target_id)` | New requests only |
| Status gate | `decide()` rejects non-pending | Re-approve blocked |
| Distinct action types | `send_reply_email` vs `send_outreach_email` | Prevents wrong dedup |
| n8n audit | `log_agent_action` on outbound | Trace only, not idempotent |

---

## Gaps

1. **No idempotency key** on n8n payload
2. **No send-once token** per ApprovalRequest execution
3. **approve endpoint** can be retried if first commit succeeded but client timed out (unlikely with sync execute, but possible)
4. **Activity scheduling** has no dedup for same sequence step
5. **execution_result** not checked before re-invoke

---

## Required M1 Contract

### ApprovalRequest execution idempotency

```python
# Before trigger_workflow:
if request.execution_result and request.execution_result.get("executed"):
    return request.execution_result  # already sent

idempotency_key = f"approval:{request.id}:send"
# Pass to n8n payload + store in execution_result
```

### n8n payload

```python
{
    "event": "outreach.approved",
    "idempotency_key": "approval:<uuid>:send",
    "contact_id": "...",
    ...
}
```

### Activity scheduling

Dedup key: `(contact_id, sequence_id, step_order)` before creating scheduled Activity.

---

## Human Approval Gate

**REQUIRED** — outbound send only via `decide(approve=True)` → `_execute_send_outreach_email`.

No autonomous send path in sales_agents.

---

*End of M0 Outbound Idempotency Contract*
