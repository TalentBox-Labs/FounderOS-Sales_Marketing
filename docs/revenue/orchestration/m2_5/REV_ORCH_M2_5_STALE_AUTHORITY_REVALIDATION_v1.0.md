# REV-ORCH M2.5 — Stale Authority Revalidation v1.0

**STATUS: FROZEN**  
**STALE_AUTHORITY_REVALIDATION = FROZEN**  
**AUTHORIZATION_AT_T1 != AUTOMATIC_AUTHORIZATION_AT_T2**

## Execution-time checks (`_execute_send_outreach_email`)

| Check | Mechanism |
|-------|-----------|
| Contact existence + tenant | `get_contact_for_tenant(db, payload.organization_id, contact_id)` |
| ApprovalRequest existence + tenant | `get_approval_for_tenant` in `decide()` |
| Approval state | `status == pending` else 409 |
| Human authority | session TenantContext + `_human_decider` |
| Stop / unsubscribe | `contact_has_stop_tags` when `workflow_kind == rev_orch_m2_follow_up` |
| Reply stop | `has_reply_stop_after_activity` vs `source_activity_id` |
| Idempotency | `execution_result.executed` + `handed_to_n8n` guard |

Human approval is necessary but not sufficient if reply or stop appeared after proposal.

Fail closed: `execution_result.executed = false`; n8n not called.
