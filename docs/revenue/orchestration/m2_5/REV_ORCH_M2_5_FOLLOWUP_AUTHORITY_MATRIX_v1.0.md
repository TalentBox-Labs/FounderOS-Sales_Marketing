# REV-ORCH M2.5 — Follow-Up Authority Matrix v1.0

**STATUS: FROZEN**

| Actor | Eligibility | Draft | File ApprovalRequest | Approve | Send n8n | Mutate Contact.status / Deal.stage |
|-------|-------------|-------|----------------------|---------|----------|-------------------------------------|
| Eligibility service | YES (deterministic) | NO | NO | NO | NO | NO |
| FollowUpWorker | NO | YES | NO | NO | NO | NO |
| WorkflowOrchestrator | dispatch only | NO | NO | NO | NO | NO |
| RevenueOrchestrationService | invokes policy + worker | NO | YES (after eligibility) | NO | NO | NO |
| Human (session tenant) | NO | NO | NO | YES | NO | NO |
| HeartbeatScheduler | scan/wake only | NO | NO (delegates to service) | NO | NO | NO |
| n8n | NO | NO | NO | NO | YES (executor) | NO |
| Client JSON org / decided_by | NO | NO | NO | NO | NO | NO |
| Legacy `build_followup_sequence` | NO | sequence template | NO | NO | NO | NO |

M1.5 frozen contracts remain: tenant, identity, proposal-only AI, human ApprovalRequest, executor-only n8n, outbound idempotency.
