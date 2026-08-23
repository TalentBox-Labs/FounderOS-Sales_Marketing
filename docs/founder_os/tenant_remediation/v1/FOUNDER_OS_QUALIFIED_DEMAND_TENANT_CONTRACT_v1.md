# QualifiedDemand Tenant Contract v1

**Entity representation:** `AgentActionLog` rows (`qualified_demand.handoff`, `.accepted`, `.rejected`)
**Canonical CRM output:** `Contact` (on accept only)

## Trusted tenant authority

Organization scope MUST come from:

1. `require_tenant_mutation()` / `resolve_tenant_context()` (session + org cookie + membership), or
2. Explicit `organization_id` passed from a route that already validated tenant context.

Client payload fields MUST NOT be treated as organization authority.

## Handoff registration

```
register_marketing_handoff(db, payload, requested_by, organization_id=<trusted>)
```

| Rule | Behavior |
|------|----------|
| Atomic org stamp | `AgentActionLog.organization_id` set on insert |
| Idempotent re-register | Same `demand_id` + same tenant → OK; cross-tenant re-register → `ValueError` |
| Production API | `POST /api/v1/marketing/qualified-demand/handoff` requires `require_tenant_mutation()` |
| Missing tenant (production) | HTTP 403 `Organization context required` |

## Accept

```
accept_qualified_demand(db, demand_id, requested_by, notes, organization_id=<trusted>)
```

| Rule | Behavior |
|------|----------|
| Handoff tenant gate | `_assert_handoff_in_tenant_scope` before mutation |
| Contact lookup | Email match filtered by `Contact.organization_id == org` |
| New contact | `_stamp_new_contact_org` from trusted org |
| Cross-tenant email | Creates separate in-tenant Contact; never merges Tenant B Contact |
| Company bind | Skipped when org present (`_resolve_company_hint` returns `None`) |
| Idempotent accept | Prior accept row org + linked Contact org must match caller tenant |

## Reject

```
reject_qualified_demand(db, demand_id, requested_by, reason, organization_id=<trusted>)
```

| Rule | Behavior |
|------|----------|
| Handoff tenant gate | `_assert_handoff_in_tenant_scope` before mutation |
| Cross-tenant reject | `ValueError: QualifiedDemand reject not in tenant scope` |
| Idempotent reject | Prior reject org must match caller tenant |

## Direct intake API

| Endpoint | Guards |
|----------|--------|
| `POST /api/v1/sales/intake/demand/accept` | `require_tenant_mutation()` → `scoped_demand_handoff()` → accept |
| `POST /api/v1/sales/intake/demand/reject` | `require_tenant_mutation()` → `scoped_demand_handoff()` → reject |

Cross-tenant demand: HTTP 404 `QualifiedDemand not found` (no existence leak).

## Operator / cockpit proxies

When tenant context resolves:

- Pass `organization_id=tenant.organization_id` to accept/reject
- `scoped_demand_handoff` enforced at router layer

When tenant context absent (legacy OF1/MDG1 env-operator):

- `optional_tenant_mutation()` returns `None`; unscoped service behavior preserved for frozen compat only

## Fail-closed read paths

| Surface | No org context |
|---------|----------------|
| `build_command_center_snapshot` | `pending_demands=[]`, `pending_demand_count=0` |
| `build_demand_contacts_snapshot` | `state=unavailable`, empty lists |
| `_pending_qualified_demands` | `[]` |

## Non-goals (this sprint)

- No `QualifiedDemand` table
- No Lead/Opportunity/Account models
- No Company migration
