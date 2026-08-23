# MC04 Tenant v2 Contract v1

**Supersedes:** tenantless HTTP assertions in frozen `tests/test_mc04_qualified_demand.py`
**Active suite:** `tests/test_mc04_qualified_demand_tenant_v2.py`

## Scope

Tenant-scoped commercial intake API contract for Marketing handoff and Sales intake.

## Requirements

| # | Requirement | Proof |
|---|-------------|-------|
| 1 | Tenant-scoped handoff succeeds | `test_tenant_scoped_handoff_succeeds` |
| 2 | Tenant-scoped accept succeeds | `test_tenant_scoped_accept_succeeds` |
| 3 | Tenant-scoped reject succeeds | `test_tenant_scoped_reject_succeeds` |
| 4 | Accept without handoff → 404 when tenant valid (scoped guard; same as not-in-tenant) | `test_accept_without_handoff_returns_not_found_with_tenant` |
| 5 | Tenantless handoff → 403, no DB row | `test_tenantless_handoff_fails_closed` |
| 6 | Tenantless accept → 403 | `test_tenantless_accept_fails_closed` |
| 7 | Tenantless reject → 403 | `test_tenantless_reject_fails_closed` |
| 8 | Cross-tenant accept → 404 | `test_cross_tenant_accept_blocked` |
| 9 | Cross-tenant reject → 404 | `test_cross_tenant_reject_blocked` |
| 10 | Same-email cross-tenant isolation | `test_same_email_contacts_isolated` |
| 11 | Direct intake no cross-tenant contact_id leak | `test_direct_intake_no_cross_tenant_contact_id` |
| 12 | Company cross-tenant bind blocked | `test_company_cross_tenant_binding_blocked` |
| 13 | MDG tenantless register → 403 | `test_tenantless_mdg_register_fails_closed` |
| 14 | Cockpit read fail-closed | `test_cockpit_read_fail_closed_without_org` |
| 15 | Mutation DB resolution failure → 503 | `test_mutation_db_resolution_failure_fails_closed` |

## Frozen MC04 historical debt

| Test | Classification |
|------|----------------|
| `test_runner_handoff_and_accept_flow` | OBSOLETE_UNSAFE_CONTRACT |
| `test_reject_creates_audit` | OBSOLETE_UNSAFE_CONTRACT |
| `test_handoff_idempotent` | OBSOLETE_UNSAFE_CONTRACT |
| `test_accept_without_handoff_rejected` | HARNESS_CONTEXT_MISSING; v2 proves 404 with tenant via `scoped_demand_handoff` (supersedes prior 422-before-tenant-gate) |

Frozen file **not modified** in v1.1.
