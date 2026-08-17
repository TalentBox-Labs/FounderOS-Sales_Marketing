# M0.5 Agent Capability Matrix v1.0

**Sprint:** REV-ORCH M0.5  
**Date:** 2026-08-17  
**Status:** FROZEN

Legend: **ALLOW** | **DENY** | **CONDITIONAL** | **NOT_APPLICABLE**

CONDITIONAL always means: tenant-scoped + policy + (where noted) human approval. Never means “agent may choose.”

---

| Actor | READ_TENANT_CONTEXT | READ_CONTACT | READ_COMPANY | READ_DEAL | RESEARCH | SCORE | GENERATE_CONTENT | PROPOSE_NEXT_ACTION | CREATE_APPROVAL_REQUEST | APPROVE | SEND_EXTERNAL | MUTATE_CONTACT_STATUS | MUTATE_DEAL_STAGE | ACCEPT_QUALIFIED_DEMAND | ACCEPT_COMMERCIAL_OUTCOME | SELECT_TENANT | SELECT_CREDENTIAL | SCHEDULE | EXECUTE_RETRY |
|-------|---------------------|--------------|--------------|-----------|----------|-------|------------------|---------------------|-------------------------|---------|---------------|-----------------------|-------------------|-------------------------|---------------------------|---------------|-------------------|----------|---------------|
| RevenueWorkflowOrchestrator | ALLOW | CONDITIONAL | CONDITIONAL | CONDITIONAL | NOT_APPLICABLE | NOT_APPLICABLE | DENY | ALLOW | ALLOW | DENY | DENY | DENY | DENY | DENY | DENY | DENY | DENY | ALLOW | CONDITIONAL |
| ResearchWorker | ALLOW | CONDITIONAL | CONDITIONAL | DENY | ALLOW | DENY | CONDITIONAL | ALLOW | DENY | DENY | DENY | DENY | DENY | DENY | DENY | DENY | DENY | DENY | DENY |
| PersonalizationWorker | ALLOW | CONDITIONAL | CONDITIONAL | DENY | DENY | DENY | ALLOW | ALLOW | DENY | DENY | DENY | DENY | DENY | DENY | DENY | DENY | DENY | DENY | DENY |
| FollowUpWorker | ALLOW | CONDITIONAL | CONDITIONAL | DENY | DENY | DENY | ALLOW | ALLOW | DENY | DENY | DENY | DENY | DENY | DENY | DENY | DENY | DENY | DENY | DENY |
| ObjectionWorker | ALLOW | CONDITIONAL | CONDITIONAL | DENY | DENY | DENY | ALLOW | ALLOW | DENY | DENY | DENY | DENY | DENY | DENY | DENY | DENY | DENY | DENY | DENY |
| LeadScoringService | ALLOW | CONDITIONAL | CONDITIONAL | CONDITIONAL | DENY | ALLOW | DENY | ALLOW | DENY | DENY | DENY | DENY | DENY | DENY | DENY | DENY | DENY | DENY | DENY |
| OutreachExecutor | ALLOW | CONDITIONAL | NOT_APPLICABLE | NOT_APPLICABLE | DENY | DENY | DENY | DENY | DENY | DENY | CONDITIONAL | DENY | DENY | DENY | DENY | DENY | DENY | NOT_APPLICABLE | CONDITIONAL |
| n8n | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE | DENY | DENY | DENY | DENY | DENY | DENY | CONDITIONAL | DENY | DENY | DENY | DENY | DENY | DENY | NOT_APPLICABLE | CONDITIONAL |
| HumanApprover | ALLOW | CONDITIONAL | CONDITIONAL | CONDITIONAL | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE | ALLOW | CONDITIONAL | ALLOW | DENY | CONDITIONAL | CONDITIONAL | CONDITIONAL | CONDITIONAL | DENY | DENY | CONDITIONAL | NOT_APPLICABLE |

---

## CONDITIONAL notes

| Cell | Condition |
|------|-----------|
| Orchestrator READ_* | TenantContext; org-scoped queries only |
| Worker READ_CONTACT/COMPANY | Same org as TenantContext; minimum fields for that worker |
| Worker GENERATE_CONTENT | Text/proposal only; no side-effect APIs |
| Orchestrator CREATE_APPROVAL_REQUEST | After schema validation of worker output |
| OutreachExecutor SEND_EXTERNAL | Only after ApprovalRequest approved + stale-authority revalidation + idempotency key |
| n8n SEND_EXTERNAL | Invoked only by executor; S4.5 inbound tenant binding; no payload tenant authority |
| Orchestrator EXECUTE_RETRY | Retry of **authorized** executor with same idempotency key; not a new send decision |
| HumanApprover mutations | Frozen A3/A4/MC04/MC06 + `is_human_approver` + membership role |
| Human SELECT_TENANT | **DENY** — tenant is server-derived even for humans (cookie/session, not body) |
| Human SELECT_CREDENTIAL | **DENY** — vault resolves org-scoped credentials; humans do not pick foreign creds |

---

## Matrix invariants

- No worker cell is ALLOW for APPROVE, SEND_EXTERNAL, MUTATE_*, ACCEPT_*, SELECT_TENANT, SELECT_CREDENTIAL.
- Peer workers have identical DENY authority columns (cognitive diversity, not authority diversity).

---

*End of M0.5 Agent Capability Matrix v1.0*
