# Founder OS COS-2 Implementation Plan

**STATUS:** BINDING FOR COS-2 IMPLEMENTATION
**Sprint:** COS-2
**Branch:** `founder-os-cos2`
**Baseline:** `founder-os-cos1-v1.0` (`c215ca5282a59d13a8e71669a5c274bf86c78f2d`)
**Architecture:** `founder-os-commercial-architecture-v1.0`

---

## Inventory (repository-grounded)

| Capability | Existing implementation | COS-2 use |
|------------|-------------------------|-----------|
| QualifiedDemand | `qualified_demand_service.py` (`qualified_demand_handoff` / `_accepted` / `_rejected` on `AgentActionLog`) | Canonical path only |
| Marketing produce | `register_marketing_handoff` + `/api/v1/marketing/qualified-demand/handoff` + MDG1 proxy | Compose payload; do not rewrite service |
| Sales intake | `accept_qualified_demand` / `reject_qualified_demand` via Operator `/api/v1/operator/actions/qualified-demand/*` | Unchanged authority |
| Founder People | `/demand` + `build_demand_contacts_snapshot` | Present source, why it matters, signals, decision, next step |
| Home | `/command` + `build_command_center_snapshot` | Demand awaiting intake + decision label |
| Activity | `/activity` + `build_activity_snapshot` | Truthful QD attribution (system recommended vs human decided) |
| Founder Profile / ICP | Missing attested ICP schema (architecture proposed only) | Workspace `Organization.name` only |
| Marketing engines | `/marketing`, Content Studio — not CRM | No new Marketing OS nav |

## Exact scope

1. Compose marketing signals onto frozen `QualifiedDemandPayload` (no persist in composer).
2. Founder read-model presentation of pending QD from **org-scoped** handoff logs, keyed by IDs already in the operator-flow snapshot.
3. Founder templates on Command Center, People, Activity.
4. Demo seed: truthful qualification/attribution + stamp `AgentActionLog.organization_id`.
5. Focused COS-2 tests + docs.

## Excluded

Models, migrations, new CRM tables, `qualified_demand_service` mutation logic, Operator HTML, M1–M4, booking/send/approvals, frozen tests, Marketing OS top-level nav, fake ARR/ICP/Audience.

## Files expected to change

- `revenue_os/services/marketing_qualified_demand.py` (new, compose-only)
- `revenue_os/services/founder_ui_read_model.py`
- `templates/founder_command.html`
- `templates/founder_demand.html`
- `templates/founder_activity.html`
- `scripts/seed_founder_demo.py`
- `tests/test_founder_os_cos2_marketing_qualified_demand.py`
- `docs/founder_os/cos2/*`

## Invariants

- QD remains an event, not a Contact.
- Handoff does not create Contact; accept uses existing MC04 spine.
- No unscoped Contact/Company/QD payload queries.
- JSON.stringify({}) and advisory booking copy untouched.
- Keep `action_type` in activity HTML (INT-D2).
