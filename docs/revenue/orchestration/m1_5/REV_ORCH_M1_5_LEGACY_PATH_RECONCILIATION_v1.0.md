# REV-ORCH M1.5 — Legacy Path Reconciliation v1.0

**STATUS: FROZEN**

## Architectural Drift Audit Summary

| Path | Classification |
|------|----------------|
| `POST /api/v1/revenue/contacts/{id}/research-to-outreach` | **CANONICAL** |
| `WorkflowOrchestrator.execute_revenue_workflow` | **CANONICAL** |
| `revenue_orchestration_service.run_research_to_outreach` | **SUBORDINATE** |
| `POST /api/v1/agents/sales/{id}/*` (5 routes) | **LEGACY_CONTAINED** (tenant required) |
| `revenue_os/api/v1/agents.py` CrewAI routes | **NOT_REACHABLE** (410/unmounted) |
| `n8n_webhooks` inbound | **GLOBAL_BY_DESIGN** (integration binding; not M1 outbound) |
| `go_to_market_orchestrator` n8n calls | **LEGACY_CONTAINED** (marketing scope; not M1) |
| `DecisionManager.approve_decision` | **LEGACY_CONTAINED** (in-memory; not ApprovalRequest) |

## UNSAFE_REACHABLE

**None** on M1 canonical mutation/outbound surfaces.

## Legacy Sales Routes (M1.1 containment)

- Require `require_tenant_context`
- `sales_agents._load_contact(..., organization_id=...)`
- Approval payloads include `organization_id`

## Residual (non-blocking)

- Legacy sales routes duplicate cold-email capability (deprecation deferred to M2)
- `n8n_webhooks._legacy_load_contact` — inbound webhook path with S4 integration tenant binding; outside M1 slice
