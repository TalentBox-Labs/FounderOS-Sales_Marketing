# Founder OS Tenant Remediation Plan v1

**Sprint:** FOUNDER OS TENANT-BOUNDARY REMEDIATION v1
**Baseline:** `founder-os-cos2-v1.0` @ `9cafb2f55352578eba6dd03ce908776744baa0b4`
**Branch:** `founder-os-tenant-remediation-v1`
**Scope:** Security / tenant-integrity only — no feature expansion

## Objective

Repair proven tenant-boundary defects from the COS-2 adversarial audit so the commercial intake path is tenant-safe before COS-3.

## Proven Defects (COS-2 Audit)

| ID | Area | Proven issue |
|----|------|--------------|
| A | `accept_qualified_demand` | Global `Contact.email` lookup without `organization_id` |
| B | `POST /api/v1/sales/intake/demand/accept` | Called accept without `scoped_demand_handoff` or trusted tenant context |
| C | `register_marketing_handoff` | `AgentActionLog.organization_id` not set atomically on insert |
| D | Company resolution | Unscoped `Company.name` / `domain` lookup during accept |
| E | Command Center / operator read models | Global pending-demand enumeration when org context absent |

## Remediation Strategy

### Defect A — Contact email resolution

- Add `_apply_contact_org_filter` and `_find_contact_by_email` scoped by trusted `organization_id`.
- Stamp new contacts with `_stamp_new_contact_org` from trusted tenant context only.
- Preserve in-tenant idempotent merge when same email exists within tenant.
- Legacy unscoped paths (`organization_id=None`) retain prior behavior for MC04 unit tests and env-operator frozen suites.

### Defect B — Direct intake accept/reject

- Introduce `require_tenant_mutation()` in `tenant_mutation_guard.py` — fail closed with HTTP 403 when org context missing.
- Wrap sales intake routes with `require_tenant_mutation()` + `scoped_demand_handoff()` before service calls.
- Pass trusted `tenant.organization_id` into service layer; never accept client-supplied org as authority.

### Defect C — Marketing handoff tenancy

- Extend `register_marketing_handoff(..., organization_id=)` to set `AgentActionLog.organization_id` on first insert.
- Production marketing handoff route requires `require_tenant_mutation()`.
- `manual_demand` passes org when tenant resolvable; demo seed passes org atomically (removed post-stamp).

### Defect D — Company tenancy (containment)

- `_resolve_company_hint` returns `None` when trusted tenant context is present — no cross-tenant Company bind.
- Document Company `organization_id` absence as deferred architecture debt.

### Defect E — Command Center fail-closed

- `operator_flow_read_model._pending_qualified_demands`: return `[]` when `org_uuid is None`.
- `founder_ui_read_model.build_command_center_snapshot`: empty pending demands when org missing.

## Protected Areas (unchanged)

- Models and migrations
- M1–M4 orchestration, booking executor, approval executor
- Outbound-send, booking, ApprovalRequest, WorkflowOrchestrator authority
- Contact.status / Deal.stage human mutation policy
- Frozen baseline tests (not modified)

## Test Plan

New suite: `tests/test_founder_os_tenant_remediation_v1.py` (10 tests).

Regression gates:

- COS-2, COS-1, UI-D2 core, D1.x init/demo, S2/S3/S4 tenant isolation
- MC04 API tests expected to fail — encoded unsafe unscoped behavior; classified, not rewritten

## Deliverables

- Surgical service/route/read-model fixes
- Six contract/attestation docs under `docs/founder_os/tenant_remediation/v1/`
- Final audit report (no commit/tag/merge)
