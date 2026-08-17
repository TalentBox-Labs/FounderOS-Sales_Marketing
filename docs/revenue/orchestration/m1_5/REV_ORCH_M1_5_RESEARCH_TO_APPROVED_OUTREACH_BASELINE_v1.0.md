# REV-ORCH M1.5 — Research-to-Approved-Outreach Baseline v1.0

**STATUS: FROZEN**  
**Parent commit:** `d36d7a2`  
**Date:** 2026-08-17  
**Baseline version:** v1.0

---

## Scope

Freezes the governed vertical slice:

```
Contact → research → qualification (recommend-only) → AI draft → ApprovalRequest
  → human approve/reject → n8n outbound → Activity + AgentActionLog
```

## 1. Canonical Entry Contract

- **App:** `runner_api:app`
- **Route:** `POST /api/v1/revenue/contacts/{contact_id}/research-to-outreach`
- **Requirement:** `require_tenant_context(http_request)` before dispatch
- **Forbidden:** parallel revenue orchestration planes bypassing `WorkflowOrchestrator`

## 2. Orchestration Authority Contract

| Layer | Owner |
|-------|-------|
| Dispatch | `WorkflowOrchestrator.execute_revenue_workflow()` |
| Registration | `REV_ORCH_M1_WORKFLOW_KEY` / `REV_ORCH_M1_AGENT_STEP` |
| Implementation | `revenue_orchestration_service.run_research_to_outreach()` (subordinate) |
| Workers | `revenue_workers` (proposal-only) |

## 3–12. Authority Contracts

See companion artifacts:
- `REV_ORCH_M1_5_AUTHORITY_MATRIX_v1.0.md`
- `REV_ORCH_M1_5_TENANT_IDENTITY_APPROVAL_ATTESTATION_v1.0.md`
- `REV_ORCH_M1_5_OUTBOUND_IDEMPOTENCY_ATTESTATION_v1.0.md`
- `REV_ORCH_M1_5_LEGACY_PATH_RECONCILIATION_v1.0.md`

## Non-Goals (M1.5)

- M2 follow-up/booking capabilities
- New SoTs, migrations, integrations, credentials
- Cockpit UI repair
- WorkflowOrchestrator wiring for non-M1 workflows

## Freeze Tests

`tests/test_rev_orch_m1_5_research_to_outreach_baseline_freeze.py`

## Change Policy

Future M2+ work MUST NOT weaken contracts 1–12 without explicit baseline version bump.
