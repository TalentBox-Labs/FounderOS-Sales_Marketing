# M0 Stale Authority Execution Contract

**Sprint:** REV-ORCH M0  
**Date:** 2026-08-17  
**Status:** DEFINED (implementation deferred to M1)

---

## Rule

**Delayed execution MUST revalidate applicable current authority and policy before any external side effect.**

A human may approve at T1. At T2 (execution or scheduled send), the system must verify conditions still hold.

---

## Revalidation Checklist (M1 outbound)

| Check | At T1 (approve) | At T2 (execute) | Current code |
|-------|-----------------|-----------------|--------------|
| Approver is human | Yes (`decide`) | **Not revalidated** | Gap |
| Approver still member of org | No | **Not checked** | Gap |
| Approver role allows action | No | **Not checked** | Gap |
| Contact still exists | Yes (executor) | Partial | `_execute_send_outreach_email` passes contact_id |
| Contact in same org | No | **Not checked** | Gap |
| Contact not opted out / rejected | No | **Not checked** | Gap |
| Deal state still eligible | N/A for email | N/A | |
| ApprovalRequest still `approved` | N/A | Single execute | OK |
| ApprovalRequest not expired | No expiry field | N/A | Gap |
| Connector credential still valid for org | No | **Not checked** | Gap |
| n8n idempotency | No | Retry may duplicate | Gap |

---

## What Existing Code Does

| Component | Behavior |
|-----------|----------|
| `approvals.decide(approve=True)` | Executes immediately in same request — minimal T1/T2 gap |
| `outreach_service.schedule_contact_sequence` | Creates future Activities — **no execution-time authority check** |
| HeartbeatScheduler | No membership validation |
| Celery retry | Retries without authority check |

---

## Required M1 Contract

Before `trigger_workflow("send-email", ...)`:

```python
def validate_outbound_execution(
    *,
    organization_id: str,
    contact_id: str,
    approval_request_id: str,
    decided_by: str,
) -> None:
    # 1. ApprovalRequest status == approved
    # 2. Contact.organization_id == organization_id
    # 3. is_human_approver(decided_by) still valid user
    # 4. Membership active with mutation-capable role
    # 5. Contact.status not in terminal/rejected states (policy)
    # 6. Idempotency key not already sent
    ...
```

---

## Scheduled Work

For Activity-based follow-ups:

- At `scheduled_at`, job must load Contact + org + approver context from Activity metadata or linked ApprovalRequest
- If validation fails: mark Activity `cancelled` + audit `stale_authority_blocked`

---

## Non-Goals (M0)

- Implement revalidation logic
- Add expiry column to ApprovalRequest

---

*End of M0 Stale Authority Execution Contract*
