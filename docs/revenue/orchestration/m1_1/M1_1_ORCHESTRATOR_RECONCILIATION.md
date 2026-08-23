# M1.1 Orchestrator Reconciliation

**Sprint:** REV-ORCH M1.1  
**Date:** 2026-08-17  
**Status:** COMPLETE

---

## Problem

M1 implemented the vertical slice correctly but routed directly to `revenue_orchestration_service.run_research_to_outreach()`, leaving `WorkflowOrchestrator._execute_agent` as stub — diverging from M0/M0.5 freeze.

## Resolution

M1 canonical route now dispatches through **WorkflowOrchestrator**:

```
POST /api/v1/revenue/contacts/{id}/research-to-outreach
  → require_tenant_context(http_request)
  → WorkflowOrchestrator.execute_revenue_workflow(REV_ORCH_M1_WORKFLOW_KEY, …)
  → registered workflow (SEQUENTIAL, step: rev_orch_m1_pipeline)
  → _handle_m1_research_to_outreach(context)
  → revenue_orchestration_service.run_research_to_outreach()  [subordinate]
  → workers → ApprovalRequest
```

## Ownership Contract

| Component | Role |
|-----------|------|
| **WorkflowOrchestrator** | Canonical dispatch/sequencing; owns workflow registration and execution envelope |
| **RevenueOrchestrationService** | SUBORDINATE workflow implementation — bounded M1 steps |
| **ResearchWorker / PersonalizationWorker** | Proposal-only capabilities |
| **ApprovalRequest** | Human authorization gate |
| **n8n** | Deterministic approved executor |

`RevenueOrchestrationService` is **not** a competing orchestrator. Future M2 steps register additional workflow keys on `WorkflowOrchestrator`.

## Registration

- `REV_ORCH_M1_WORKFLOW_KEY = "rev_orch_research_to_outreach"`
- `REV_ORCH_M1_AGENT_STEP = "rev_orch_m1_pipeline"`
- `WorkflowOrchestrator.seed_revenue_workflows()` called at `runner_api` startup
- Response includes `orchestrator: "WorkflowOrchestrator"` and `workflow_execution_id`

## Files Changed

- `revenue_os/agents/orchestration.py` — revenue workflow registry + M1 handler
- `runner_api_routers/revenue_orchestration.py` — route through orchestrator
- `runner_api.py` — seed revenue workflows on startup

## Preserved

TenantContext, IdentityContext, ApprovalRequest authority, outbound idempotency, audit provenance, M1 behavior.
