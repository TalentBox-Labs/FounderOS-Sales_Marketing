# REV-ORCH M3 — Governed Reply Handling v1

**Parent baseline:** `2cefad0` (M2 + M2.5 freeze)  
**Branch:** `rev-orch-m3`

## Flow

```
n8n POST /webhooks/n8n/email.replied
  → X-N8N-Secret tenant binding (payload org ignored)
  → tenant-scoped Contact resolution
  → inbound Activity EMAIL_REPLY + EmailActivity.message_id
  → lead_score boost (existing S4 signal; not status)
  → wake_inbound_reply_handling
  → WorkflowOrchestrator.execute_revenue_workflow(rev_orch_inbound_reply_handling)
  → ReplyAnalysisWorker (proposal-only)
  → deterministic reply_routing
  → AgentActionLog assessment
  → optional Contact.tags opt-out token (M2.5 stop contract)
```

No booking. No Contact.status / Deal.stage / QualifiedDemand acceptance.

## Canonical surfaces

| Role | Implementation |
|------|----------------|
| Inbound transport | `POST /webhooks/n8n/email.replied` |
| Wake | `wake_inbound_reply_handling` (SUBORDINATE) |
| Orchestrator | `WorkflowOrchestrator` / `rev_orch_inbound_reply_handling` |
| Inspect | `GET /api/v1/revenue/contacts/{id}/reply/latest-assessment` |
| Worker | `run_reply_analysis_worker` |
| Policy | `route_reply_assessment` |
