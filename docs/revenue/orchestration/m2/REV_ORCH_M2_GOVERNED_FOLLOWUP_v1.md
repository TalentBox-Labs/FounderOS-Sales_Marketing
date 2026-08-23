# REV-ORCH M2 — Governed Follow-Up Lifecycle v1

**Parent baseline:** `b0004a4` (M1.5 freeze)  
**Branch:** `rev-orch-m2`

## Flow

```
Initial outbound Activity (M1 approved send)
  → deterministic eligibility evaluation
  → FollowUpWorker (proposal-only)
  → ApprovalRequest (send_outreach_email + M2 payload metadata)
  → human approve/reject
  → stale authority revalidation at execution
  → n8n EXECUTOR_ONLY send
  → outbound Activity + AgentActionLog
  → repeat (max 2 follow-ups) or stop on reply/DNC
```

## Canonical entry

| Surface | Route |
|---------|-------|
| Eligibility inspect | `GET /api/v1/revenue/contacts/{id}/follow-up/eligibility` |
| Proposal | `POST /api/v1/revenue/contacts/{id}/follow-up/propose` |
| Orchestrator | `WorkflowOrchestrator.execute_revenue_workflow(REV_ORCH_M2_WORKFLOW_KEY, …)` |
| Workflow key | `rev_orch_follow_up_to_outreach` |
| Step | `rev_orch_m2_pipeline` |

## Components

| Role | Implementation |
|------|----------------|
| Orchestrator | `WorkflowOrchestrator` |
| Eligibility | `follow_up_eligibility.evaluate_follow_up_eligibility` |
| Cognition | `FollowUpWorker` (`revenue_workers.run_followup_worker`) |
| Human gate | `ApprovalRequest` (reused) |
| Executor | `approvals._execute_send_outreach_email` |
| Connector | n8n `send-email` (EXECUTOR_ONLY) |

## Cadence (bounded MVP)

- Step 1: 3 days after last outbound
- Step 2: 7 days after last outbound
- Maximum 2 follow-ups per contact chain

## No new SoTs

State represented via existing `Activity`, `ApprovalRequest.payload`, and `AgentActionLog`.
