# M0 Tenant Context Propagation Audit

**Sprint:** REV-ORCH M0  
**Date:** 2026-08-17  
**Verdict:** **PARTIAL** — gaps defined, not blocking M1 with restrictions

---

## TenantContext Source

**Path:** `revenue_os/services/tenant_context.py`  
**Resolution:** `revenue_os/services/tenant_resolution.py` — server-derived from session + org cookie

---

## Propagation by Path

| Path | TenantContext present? | Evidence | Gap |
|------|------------------------|----------|-----|
| CRM routes (`runner_api_routers/crm.py`) | **YES** | S3.5 frozen tests | None |
| Cockpit / operator flow | **YES** | UI2.5 / OF1.5 | None |
| Manual demand / QD / CO | **YES** | MDG/MC04/MC06 routers | None |
| Integrations / webhooks | **YES** | S4.5 frozen | None |
| sales_agents via agents router | **NO** | ID-only contact lookup | **HIGH for M1** |
| WorkflowOrchestrator execute | **NO** | Context dict only | **MEDIUM for M1** |
| ApprovalRequest service | **NO** | Global SessionLocal | **MEDIUM for M1** |
| EventBus emit/subscribe | **NO** | Payload-dependent | **MEDIUM** |
| HeartbeatScheduler jobs | **NO** | Global Contact query | **HIGH for multi-tenant** |
| Celery tasks | **NO** | No org in task args | **MEDIUM** |
| n8n outbound `trigger_workflow` | **Partial** | contact_id in payload | Must validate org at execute |
| AIService / OpenAI | **N/A** | GLOBAL_BY_DESIGN credential | Data must be tenant-scoped before call |

---

## Critical Question

**Can TenantContext be lost between initial request and delayed execution?**

**YES** — confirmed paths:

1. **ApprovalRequest approve → n8n send** — no org revalidation at execution
2. **Activity scheduled via outreach_service** — `scheduled_at` with no org envelope
3. **Heartbeat jobs** — query all contacts across orgs
4. **Celery retry** — no TenantContext in task envelope

---

## Required Future Pattern (M1+)

Conceptual **ScheduledWorkEnvelope** (not necessarily new table):

```python
{
  "organization_id": "<server-bound>",
  "actor_identity_ref": "<IdentityContext snapshot or id>",
  "action_type": "send_outreach_email",
  "target_type": "contact",
  "target_id": "<uuid>",
  "approval_request_id": "<uuid>",
  "provenance": {"workflow_id": "...", "step": "..."},
  "policy_version": "rev-orch-m1"
}
```

---

## Existing Structures That Can Carry Context

| Object | Can carry org? | Today |
|--------|----------------|-------|
| `ApprovalRequest.payload` | **Yes** — add `organization_id` key | Not enforced |
| `Activity` | **Yes** — via Contact.organization_id join | No scheduler revalidation |
| `AgentActionLog` | **Yes** — detail JSON | Best-effort |
| HeartbeatRun | Partial | Job-level only |
| Workflow execution context dict | **Yes** | Not populated |

**Recommendation:** Use `ApprovalRequest.payload["organization_id"]` + Contact join validation at execution — **no new persistent model for M1**.

---

## M1 Requirement

All canonical orchestration entrypoints MUST:

1. Resolve TenantContext before any contact/deal lookup
2. Reject ID-only cross-tenant access (S3.5 pattern)
3. Embed `organization_id` in approval payload and validate at execution

---

*End of M0 Tenant Context Propagation Audit*
