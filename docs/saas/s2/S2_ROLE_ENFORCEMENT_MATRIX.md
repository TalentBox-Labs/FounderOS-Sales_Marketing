# SaaS S2 — Role Enforcement Matrix

| Role | Read (cockpit/operator) | Bounded mutations (S2 slice) |
|------|-------------------------|------------------------------|
| OWNER | PASS | PASS |
| ADMIN | PASS | PASS |
| MEMBER | PASS | PASS |
| VIEWER | PASS | **BLOCKED** (403) |

## Enforcement point

`require_tenant_mutation_role()` in `tenant_resolution.py`  
`optional_tenant_mutation()` in `tenant_mutation_guard.py`

## Not in S2 scope

Enterprise RBAC, SSO, admin-only ownership transfer, billing admin.

## Frozen domain preserved

Membership role gates tenant proxy endpoints only. Frozen services (`accept_qualified_demand`, `apply_contact_status_update`, etc.) retain existing `HUMAN_ONLY` checks.
