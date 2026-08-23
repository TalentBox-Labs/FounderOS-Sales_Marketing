# REV-ORCH M2.5 — Governed Follow-Up Baseline v1.0

**STATUS: FROZEN**  
**Parent commit:** `b0004a4` (M1.5 freeze)  
**Branch:** `rev-orch-m2`  
**Baseline version:** v1.0

## Frozen flow

```
completed outbound Activity (M1 approved send)
  → evaluate_follow_up_eligibility (deterministic)
  → FollowUpWorker (proposal-only)
  → ApprovalRequest (send_outreach_email, workflow_kind=rev_orch_m2_follow_up)
  → human approve/reject via session TenantContext
  → execution-time revalidation
  → n8n send-email (EXECUTOR_ONLY)
  → outbound Activity + AgentActionLog
  → next eligibility (reply/stop/cadence)
```

## Canonical surfaces

| Role | Implementation |
|------|----------------|
| API propose | `POST /api/v1/revenue/contacts/{id}/follow-up/propose` |
| API eligibility | `GET /api/v1/revenue/contacts/{id}/follow-up/eligibility` |
| Orchestrator | `WorkflowOrchestrator.execute_revenue_workflow(REV_ORCH_M2_WORKFLOW_KEY)` |
| Workflow key | `rev_orch_follow_up_to_outreach` |
| Step | `rev_orch_m2_pipeline` |
| Implementation | `run_follow_up_to_outreach` / `_run_follow_up_proposal` |
| Scheduler wake | `job_scan_follow_up_eligibility` → `run_follow_up_proposal_scheduled` (SUBORDINATE; files ApprovalRequest only) |

## Frozen contracts (v1.0)

| Contract | Value |
|----------|-------|
| SCHEDULER_AUTHORITY | INFRASTRUCTURE_ONLY |
| SERVER_TRUSTED_TENANT_RECONSTRUCTION | FROZEN |
| STALE_AUTHORITY_REVALIDATION | FROZEN |
| REPLY_STOP_CONTRACT | FROZEN |
| FOLLOWUP_STOP_CONTRACT | FROZEN |
| FOLLOWUP_CADENCE_v1 | 2 steps; 3d / 7d |
| AI_AUTHORITY | PROPOSAL_ONLY |
| Human approval | REQUIRED (ApprovalRequest reused) |
| n8n | EXECUTOR_ONLY |
| FOLLOWUP_IDEMPOTENCY | FROZEN |
| CANONICAL_FOLLOWUP_ENGINE | M2 governed workflow |
| NEW_FOLLOWUP_SOT | PROHIBITED_FOR_v1 |

## State representation

Activity + ApprovalRequest.payload + AgentActionLog. No dedicated follow-up SoT.

## Non-goals (explicit)

Booking, objection-handling automation, cadence expansion, autonomous send, new models/migrations, UI redesign, M1.5 contract changes.
