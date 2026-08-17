# REV-ORCH M1 — Research-to-Approved-Outreach Vertical Slice

**Sprint:** REV-ORCH M1  
**Date:** 2026-08-17  
**Status:** IMPLEMENTED / FROZEN  
**Branch:** `rev-orch-m1`

---

## Summary

M1 implements one governed revenue workflow on an **existing tenant-scoped Contact**:

```
Contact → ResearchWorker → Qualification (recommend-only) → PersonalizationWorker (draft)
  → ApprovalRequest (pending) → Human approve/reject → n8n outbound executor → Activity + AgentActionLog
```

No new persistent SoTs, migrations, credentials, or external integrations were added.

---

## Canonical Entry Point

| Surface | Role |
|---------|------|
| **`runner_api:app`** | Production API (Dockerfile) |
| **`POST /api/v1/revenue/contacts/{contact_id}/research-to-outreach`** | M1 vertical slice trigger |
| **`POST /api/v1/approvals/{id}/approve`** | Human approval gate |
| **`POST /api/v1/approvals/{id}/reject`** | Human rejection |

`revenue_os/main.py` and quarantined `revenue_os/api/v1/agents.py` (410) are **not** used for M1.

---

## Architecture

```
TenantContext (session + org cookie, server-derived)
        │
        v
revenue_orchestration_service.run_research_to_outreach()
        │
        ├── get_contact_for_tenant()          [CRM SoT read]
        ├── run_research_worker()             [proposal/evidence]
        ├── score_contact()                   [recommend-only; status_changed=False]
        ├── run_personalization_worker()      [AI draft; no send]
        └── request_approval()                [ApprovalRequest pending]
                │
                v (human approve)
        approvals.decide() → _execute_send_outreach_email()
                │
                v
        n8n.trigger_workflow("send-email")    [executor only]
                │
                v
        Activity (outbound email) + AgentActionLog
```

**Orchestrator:** `revenue_orchestration_service` (M1 service layer). `WorkflowOrchestrator._execute_agent` remains a stub; M1 does not route through it.

---

## State Machine (conceptual, response fields — not a new DB SoT)

| State | Meaning |
|-------|---------|
| `CONTACT_SELECTED` | Tenant-scoped contact resolved |
| `RESEARCH_COMPLETED` | ResearchWorker finished |
| `QUALIFICATION_COMPLETED` | `score_contact` recommend-only |
| `DRAFT_CREATED` | PersonalizationWorker draft |
| `APPROVAL_PENDING` | `ApprovalRequest` filed, status=pending |
| `APPROVED` / `REJECTED` | Human decision via approvals API |
| `OUTBOUND_HANDOFF` | n8n invoked on approve |
| `OUTBOUND_RECORDED` | Outbound Activity + audit log |

---

## Capability Boundaries

| Capability | Input | Output | Mutation authority |
|------------|-------|--------|-------------------|
| **Research** | Authorized Contact + org | Evidence/signals dict | Activity NOTE only |
| **Qualification** | Contact | Score + suggested_status | Updates lead_score only; **no** status mutation |
| **Personalization** | Contact + research | Draft body (AI) | None |
| **Approval** | Proposal payload | Human decision | Executes outbound only when approved |
| **Outbound** | Approved payload | n8n handoff | Activity on success |

Workers are **proposal-only**; orchestrator files `ApprovalRequest`.

---

## Authority Matrix

| Actor | Research | Score | Draft | File Approval | Approve | Send |
|-------|----------|-------|-------|---------------|---------|------|
| Human (session tenant) | via API | — | — | — | YES | via approve |
| ResearchWorker | YES | — | — | — | NO | NO |
| PersonalizationWorker | — | — | YES | via orchestrator | NO | NO |
| Agent/AI identity | — | — | — | — | NO | NO |
| n8n / webhook | — | — | — | — | NO | executor only |

---

## Tenant Model

- All M1 paths require `require_tenant_context(http_request)` on the orchestration route.
- Contact access via `get_contact_for_tenant(db, org_id, contact_id)`.
- Approval access via `get_approval_for_tenant(db, org_id, request_id)` when session tenant present.
- Client-supplied `organization_id` in body is **ignored**.
- Cross-tenant contact/approval access returns 422/404.

---

## AI Boundary

- `AIService.generate_cold_email` used for draft text only.
- Global OpenAI env configuration (not per-tenant isolation).
- No LLM database tools or unrestricted tool calling.
- AI output never sends directly; always passes through `ApprovalRequest`.

---

## Approval Boundary

- `request_approval(..., organization_id=...)` embeds org in payload.
- `decide(..., tenant=...)` binds approver from server `TenantContext` identity.
- `_validate_outbound_payload` re-validates contact tenant before n8n.
- Idempotent re-approve: skips n8n if `execution_result.executed` + `handed_to_n8n`.
- `idempotency_key` passed to n8n payload.

---

## Outbound Boundary

- n8n is **executor only** — not orchestrator.
- Only **approved** `send_outreach_email` actions invoke `_execute_send_outreach_email`.
- Rejected/pending proposals never reach n8n.

---

## Audit Provenance

| Event | Mechanism |
|-------|-----------|
| Workflow start | `AgentActionLog` (`rev_orch_workflow_started`) |
| Research | `AgentActionLog` + Activity NOTE |
| Qualification | `AgentActionLog` (`rev_orch_qualification`) |
| Draft | Activity NOTE + `AgentActionLog` (`worker_personalize`) |
| Approval filed | `AgentActionLog` (`approval_requested`) |
| Decision | `AgentActionLog` + ApprovalRequest fields |
| Outbound | Activity EMAIL + n8n payload audit in execution_result |

`AgentActionLog.organization_id` populated when org known.

---

## Legacy Containment

| Path | M1 disposition |
|------|----------------|
| `revenue_os/api/v1/agents.py` CrewAI routes | 410 / unmounted (M0) |
| `runner_api_routers/agents.py` sales_agents (ID-only) | **Not used** by M1; residual risk documented |
| Celery `score_lead_background` | Not invoked by M1 |
| `WorkflowOrchestrator._execute_agent` stub | Not wired in M1 |

---

## Files Changed

| File | Change |
|------|--------|
| `revenue_os/services/revenue_workers.py` | NEW — ResearchWorker, PersonalizationWorker |
| `revenue_os/services/revenue_orchestration_service.py` | NEW — M1 orchestration flow |
| `runner_api_routers/revenue_orchestration.py` | NEW — canonical API route |
| `revenue_os/services/approvals.py` | Tenant-scoped decide, outbound validation, idempotency |
| `revenue_os/services/activity_log.py` | `organization_id` on AgentActionLog |
| `revenue_os/services/tenant_scoped_access.py` | `get_approval_for_tenant` |
| `runner_api_routers/approvals.py` | Session tenant on list/approve/reject |
| `runner_api.py` | Mount revenue_orchestration router |
| `tests/test_rev_orch_m1_research_to_outreach.py` | NEW — 10 focused tests |

---

## Tests

**File:** `tests/test_rev_orch_m1_research_to_outreach.py`

Covers: happy path, approval gate, reject/no-send, cross-tenant contact/approval, org spoof, agent cannot approve, n8n idempotency, legacy route not mounted.

External boundaries mocked: OpenAI (`generate_cold_email`), n8n (`trigger_workflow`). Tenant/authority enforcement **not** mocked.

---

## Known Risks

| Severity | Risk |
|----------|------|
| **Medium** | `runner_api_routers/agents.py` sales routes still use ID-only contact load (pre-M1 path) |
| **Medium** | `decide()` without session tenant falls back to client `decided_by` (legacy API-key path) |
| **Low** | SQLite test DB returns naive `created_at`; production Postgres uses timezone-aware timestamps |
| **Low** | `WorkflowOrchestrator` stub not wired — future M2 should unify |

---

## Deferred

- Follow-up capability worker
- Booking capability
- Background/scheduler-driven M1 runs (tenant provenance not guaranteed on all heartbeat paths)
- Per-tenant OpenAI configuration
- Wiring M1 through `WorkflowOrchestrator` step registry

---

## Change Budget Attestation

| Category | Count |
|----------|-------|
| New persistent SoTs | 0 |
| Database migrations | 0 |
| New external integrations | 0 |
| Credentials added | 0 |
| Frozen contract changes | 0 |
