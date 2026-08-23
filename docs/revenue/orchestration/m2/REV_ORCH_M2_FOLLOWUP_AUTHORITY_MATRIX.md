# REV-ORCH M2 — Follow-Up Authority Matrix

| Actor | Follow-Up Eligibility | Draft Content | File ApprovalRequest | Approve Send | Execute n8n | Mutate Contact.status |
|-------|----------------------|---------------|---------------------|--------------|-------------|----------------------|
| FollowUpWorker | NO | YES (proposal) | NO | NO | NO | NO |
| Eligibility service | YES (deterministic) | NO | NO | NO | NO | NO |
| WorkflowOrchestrator | NO (dispatches) | NO | NO | NO | NO | NO |
| Human (session tenant) | NO | NO | NO | YES | NO | NO |
| Scheduler (heartbeat) | NO (scan only) | NO | NO (files via service) | NO | NO | NO |
| n8n | NO | NO | NO | NO | YES (executor) | NO |
| AI (direct) | NO | NO | NO | NO | NOT_REACHABLE | NOT_REACHABLE |

Frozen M1.5 contracts unchanged: tenant authority, identity authority, proposal-only AI, human ApprovalRequest, executor-only n8n, outbound idempotency.
