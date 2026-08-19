# Founder OS COS-1 Implementation Plan

**STATUS:** BINDING FOR COS-1 IMPLEMENTATION
**Sprint:** COS-1
**Branch:** `founder-os-cos1`
**Baseline:** `99a657a2ba3532fb91d6c8030d1b4d733a295081`
**Architecture:** COS-ARCH-v1 + v1.1 CONDITIONAL GO

---

## Inventory (Phase 1)

| Capability | Route | Read model | Template | Authority | Tenant | Tests |
|------------|-------|------------|----------|-----------|--------|-------|
| Home | `/command` | `build_command_center_snapshot` | `founder_command.html` | read | org_id | UI-D1.5 nav |
| People | `/demand` | `build_demand_contacts_snapshot` | `founder_demand.html` | read | operator flow org filter | UI-D1 |
| Person | `/contacts/{id}` | `build_contact_workspace_snapshot` + `attach_safe_booking` | `founder_contact.html` | M1/M2 propose; M4 propose | `get_contact_for_tenant` | UI-D2 30 |
| Approvals | `/pending-approvals` | `build_approvals_snapshot` | `founder_approvals.html` | empty POST | list_requests org | UI-D2 |
| Activity | `/activity` | `build_activity_snapshot` | `founder_activity.html` | read | AgentActionLog.organization_id | INT-D2 labels |
| Operator | `/operator` | operator_flow | `operator.html` | human actions | org | OF1 — **out of COS-1 feature work** |
| QD | operator / demand | AgentActionLog | demand + operator | human accept | org | MC04 |
| Booking | contact + M4 APIs | `_build_booking_panel` | contact booking panel | ApprovalRequest | connector + tenant | UI-D2 / M4.5 |

**Gaps (presentation only):** Home/People/Person mix internal codes; `contact.company` may be an ORM object; demand rows lack company/attention copy; activity shows raw types (must **keep** types in HTML for INT-D2); Command vs Cockpit — do not merge.

---

## Exact scope

- Server presentation fields on **existing** founder read models.
- Template hierarchy/copy for founder_* screens.
- Focused COS-1 tests.
- Docs under `docs/founder_os/cos1/`.

## Excluded

- Models, migrations, M1–M4 executors, calendar providers, `/cockpit` features, SPA, new SoT, frozen tests, operator rewrite, unscoped Company/Deal lists, Contact.status writes.

## Files expected to change

- `revenue_os/services/founder_ui_read_model.py`
- `templates/founder_command.html`
- `templates/founder_demand.html`
- `templates/founder_contact.html`
- `templates/founder_approvals.html`
- `templates/founder_activity.html`
- `templates/base.html` (nav aria / People subtitle only if Command Center string preserved)
- `tests/test_founder_os_cos1_commercial_spine.py` (new)
- `docs/founder_os/cos1/*`

`runner_api_routers/ui.py` only if a presentation attach is required (prefer read-model-only).

## Invariants

- runner_api only; TenantContext/session org; JSON.stringify({}); no client identity.
- UI-D2 booking behavior unchanged.
- Keep `data-testid` values used by UI-D1/D2.
- Keep `Command Center` nav string (UI-D1.5).
- Keep `action_type` in activity HTML (INT-D2).
- Advisory next action remains labeled advisory.

## Contained risks (v1.1)

C1–C4, H1–H2, H4, H6–H8 remain bounded. Do not expand into H3/H5.
