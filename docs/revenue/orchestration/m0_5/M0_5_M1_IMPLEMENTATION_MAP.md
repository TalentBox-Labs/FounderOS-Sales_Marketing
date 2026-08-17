# M0.5 M1 Implementation Map

**Sprint:** REV-ORCH M0.5  
**Date:** 2026-08-17  
**Status:** COMPLETE map — do not implement in M0.5

---

## Target slice

Existing Contact → research/enrich → score/recommend → AI draft → ApprovalRequest → human approval → n8n outbound → Activity/audit

Canonical API: `runner_api:app` only.

---

## Modules reused unchanged (intent)

| Module | Use |
|--------|-----|
| `revenue_os/services/ai_service.py` | LLM generate |
| `revenue_os/services/linkedin_enrichment.py` | Enrich |
| `revenue_os/services/lead_scoring_service.py` | Score suggest |
| `revenue_os/services/approvals.py` | request_approval / decide / EXECUTORS |
| `revenue_os/integrations/n8n.py` | send-email |
| `revenue_os/models/contact.py` | SoT |
| `revenue_os/models/approvals.py` | ApprovalRequest |
| `revenue_os/models/automation_state.py` AgentActionLog | Audit |
| `runner_api_routers/approvals.py` | Human decide |

---

## Modules requiring modification

| Module | Change |
|--------|--------|
| `sales_agents.py` | Tenant-scoped Contact load; split draft vs file-approval; populate org in payload |
| `runner_api_routers/agents.py` | Require TenantContext / session on `/sales/{contact_id}/*`; reject cross-tenant IDs |
| `approvals.py` `decide` / `_execute_send_outreach_email` | Revalidate org + membership; idempotency_key; skip if already executed |
| `activity_log.py` | Pass organization_id |
| `orchestration.py` `_execute_agent` | Optional: wire ResearchWorker + PersonalizationWorker; else M1 uses explicit sequential service calls from a thin orchestrator function |

---

## Modules potentially added (code, not SoT)

| Possible | Purpose |
|----------|---------|
| `revenue_os/services/revenue_workflow.py` (or similar) | Thin WorkflowOrchestrator adapter: tenant → research → score → draft → approval. **Not a new SoT.** |
| Validator helpers | Strip prohibited proposal fields |

Prefer extending `WorkflowOrchestrator` over a second orchestrator.

---

## Routes touched

| Route | App |
|-------|-----|
| `POST /api/v1/agents/sales/{contact_id}/research` | runner_api |
| `POST /api/v1/agents/sales/{contact_id}/cold-email` | runner_api |
| `POST /api/v1/approvals/{id}/approve` | runner_api |
| Optional `POST /api/v1/agents/workflows/{id}/execute` | runner_api — only if stub wired |

Do **not** add routes on `revenue_os/main.py`.

---

## Services touched

sales_agents, ai_service (call only), linkedin_enrichment, lead_scoring_service, approvals, n8n, activity_log, tenant_resolution, mutation_authority (approve path).

---

## Paths

| Concern | Path |
|---------|------|
| ApprovalRequest | existing model + payload.organization_id |
| TenantContext | resolve on agents routes; join Contact.organization_id |
| Activity | existing NOTE / post-send Activity if already used |
| n8n outbound | `_execute_send_outreach_email` only |
| Audit | AgentActionLog with organization_id |

---

## Tests required (M1, not M0.5)

1. Cross-tenant contact_id rejected on research/cold-email
2. AI/agent cannot approve
3. Worker output cannot trigger n8n without ApprovalRequest
4. Double-approve does not double-send
5. requested_by server-bound
6. Frozen A3/A4/MC04/MC06 still blocked for workers
7. S3.5 / S4.5 still pass

---

## Non-goals (M1)

New SoT, new persistent domain model, CrewAI integration, tool calling, auto-qualify, calendar, LinkedIn auto-send, seven workers.

---

*End of M0.5 M1 Implementation Map*
