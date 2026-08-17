# REV-ORCH M1.5 — Tenant / Identity / Approval Attestation v1.0

**STATUS: FROZEN**  
**Parent commit:** `d36d7a2`

## Tenant Authority

- Resolved via `require_tenant_context` / `resolve_tenant_context` + org cookie
- Contact access: `get_contact_for_tenant(db, org_id, contact_id)`
- Approval access: `get_approval_for_tenant(db, org_id, request_id)`
- Client `organization_id` in body: **ignored**

## Identity Authority

- Human approver bound from `TenantContext.identity` (display_name / email)
- `_human_decider`: raises if `tenant is None`
- Approve/reject routes: `require_tenant_context` mandatory

## Verification

| Attack | Result |
|--------|--------|
| Cross-tenant contact | 422 BLOCKED |
| Cross-tenant approval | 403/404 BLOCKED |
| Client org spoof | IGNORED |
| Client decided_by spoof | 403 BLOCKED |
| Agent decided_by | 403 BLOCKED |

## Evidence

- `tests/test_rev_orch_m1_5_research_to_outreach_baseline_freeze.py`
- `tests/test_rev_orch_m1_research_to_outreach.py`
- `tests/test_rev_orch_m1_1_orchestrator_reconciliation.py`
