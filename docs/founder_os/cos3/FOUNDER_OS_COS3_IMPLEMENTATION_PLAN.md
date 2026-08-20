# Founder OS COS-3 Implementation Plan

**STATUS:** IMPLEMENTED
**Sprint:** COS-3 Commercial Decision Loop
**Branch:** `founder-os-cos3`
**Baseline:** `founder-os-tenant-remediation-v1.1` (`0d436d3bebad08d059450cb13e119d72a1c989f1`)

**Scope reconciliation:** See `FOUNDER_OS_COS3_SCOPE_RECONCILIATION.md`. Frozen roadmap historically labeled COS-3 as Company/Deal workspaces; this sprint implements the Commercial Decision Loop (roadmap sequence supersession, not an architecture model deviation).

## Objective

Compose a Founder-facing **Commercial Decision Loop** on Command Center from existing commercial spine evidence — without new persistent systems of truth.

```
Marketing Signal → QualifiedDemand → Founder Decision → Existing Sales/Approval Action → Outcome/Activity
```

## Inventory (repository-grounded)

| Capability | Existing | COS-3 use |
|------------|----------|-----------|
| QualifiedDemand | `AgentActionLog` + MC04 services | Decision item (intake) |
| Approvals | `ApprovalRequest` + `list_requests` | Decision item (human authority) |
| Meeting interest / booking eligibility | Reply assessment logs + UI-D2 | Ready / informational items |
| Follow-up eligibility | Rev-orch inspect | Ready items |
| Outcomes | QD accept/reject + commercial outcome + approval_* logs | Completed items |
| Command Center | `build_command_center_snapshot` | Primary decision surface |
| Tenant guards | remediation v1.1 | Fail-closed reads; no mutation bypass |

## Scope

1. Compose-only module `commercial_decision_loop.py` (no DB writes).
2. Extend Command Center snapshot with `decision_items` + `decision_loop` summary.
3. Fail closed when `organization_id` missing (empty decisions + unavailable state).
4. Jinja presentation on `/command` — route to existing `/demand`, `/pending-approvals`, `/contacts/{id}`, `/activity`.
5. Focused COS-3 tests + docs.

## Excluded

New models/migrations, CRM tables, scoring/AI confidence, revenue estimates, mutation proxies on Command Center, Marketing/Sales/Revenue OS nav, weakening tenant remediation.

## Files

- `revenue_os/services/commercial_decision_loop.py` (new)
- `revenue_os/services/founder_ui_read_model.py`
- `templates/founder_command.html`
- `tests/test_founder_os_cos3_commercial_decision_loop.py` (new)
- `docs/founder_os/cos3/*` (including `FOUNDER_OS_COS3_SCOPE_RECONCILIATION.md`)
