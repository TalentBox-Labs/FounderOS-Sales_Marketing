# REV-ORCH M1.5 — Authority Matrix v1.0

**STATUS: FROZEN**

| Actor / Component | Research | Qualify | Draft | File Approval | Approve | Send Outbound | Mutate Contact Status | Mutate Deal |
|-------------------|----------|---------|-------|---------------|---------|---------------|----------------------|-------------|
| Human (session tenant) | via API trigger | — | — | — | YES | via approve | frozen paths only | frozen paths only |
| WorkflowOrchestrator | dispatch | dispatch | dispatch | dispatch | NO | NO | NO | NO |
| ResearchWorker | YES | NO | NO | NO | NO | NO | NO (NOTE only) | NO |
| Qualification (`score_contact`) | — | recommend | NO | NO | NO | NO | NO (score only) | NO |
| PersonalizationWorker | — | — | YES (AI) | NO | NO | NO | NO | NO |
| AIService | — | — | text only | NO | NO | NO | NO | NO |
| ApprovalRequest | — | — | — | YES | human only | gate | NO | NO |
| n8n | — | — | — | — | NO | executor | NO | NO |
| Client payload fields | NO | NO | NO | NO | NO | NO | NO | NO |

**AI Authority:** PROPOSAL_ONLY  
**Human Approval Authority:** server TenantContext identity only
