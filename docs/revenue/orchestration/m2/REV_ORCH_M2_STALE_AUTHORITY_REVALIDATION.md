# REV-ORCH M2 — Stale Authority Revalidation

Before follow-up outbound execution (`_execute_send_outreach_email`), when `workflow_kind == rev_orch_m2_follow_up`:

1. **Tenant ownership** — `get_contact_for_tenant(db, org_id, contact_id)` (existing M1 validation)
2. **Stop tags** — `contact_has_stop_tags(contact)` blocks send
3. **Reply state** — `has_reply_stop_after_activity(db, contact_id, source_activity_id)` blocks send

T1 authorization (proposal at eligibility time) does not automatically authorize T2 send. Human approval is necessary but not sufficient if reply/stop conditions appeared after proposal.

Execution failure is recorded in `ApprovalRequest.execution_result` with `executed: false` — fail closed, no silent send.
