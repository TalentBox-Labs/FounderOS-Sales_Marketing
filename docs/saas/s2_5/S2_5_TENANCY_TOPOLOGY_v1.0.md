# S2.5 — Tenancy Topology v1.0

**Baseline:** Organization / Tenant Isolation v1.0  
**Status:** FROZEN

## Layer stack

```
AUTHENTICATION (bcrypt + httpOnly JWT cookie)
    ↓
IDENTITY (IdentityContext — S1.5 frozen)
    ↓
ORGANIZATION (canonical tenant boundary)
    ↓
MEMBERSHIP (user ↔ organization + role)
    ↓
TENANT CONTEXT (TenantContext — server-derived)
    ↓
TENANT DATA ACCESS (scoped reads + org_id filters)
    ↓
TENANT MUTATION GUARDS (optional_tenant_mutation → scoped_*)
    ↓
FROZEN DOMAIN OPERATIONS (MC04.5, MC06.5, A3.5, A4.5 — unchanged)
    ↓
AUDIT PROVENANCE (AgentActionLog.organization_id)
```

## Component map

| Layer | Module | Key symbols |
|-------|--------|---------------|
| User | `revenue_os/models/user.py` | `User` |
| Organization | `revenue_os/models/organization.py` | `Organization`, `OrganizationMembership` |
| IdentityContext | `revenue_os/services/identity_context.py` | `IdentityContext`, `PrincipalKind`, `bind_requested_by()` |
| TenantContext | `revenue_os/services/tenant_context.py` | `TenantContext` |
| Resolution | `revenue_os/services/tenant_resolution.py` | `resolve_tenant_context()`, `ORGANIZATION_COOKIE` |
| Scoped access | `revenue_os/services/tenant_scoped_access.py` | `get_*_for_tenant()`, stamp helpers |
| Mutation guards | `revenue_os/services/tenant_mutation_guard.py` | `optional_tenant_mutation()`, `scoped_*()` |
| Bootstrap | `revenue_os/services/tenant_bootstrap.py` | `bootstrap_tenant_if_needed()` |
| Tenant API | `runner_api_routers/tenant.py` | `/api/v1/tenant/me`, `/select` |

## Authentication → tenant path

1. `POST /login` or `/api/v1/identity/login` → JWT in `founder_os_identity` cookie
2. `identity_from_request()` → `IdentityContext` (HUMAN)
3. `resolve_tenant_context()` → membership lookup + org cookie validation
4. `TenantContext` available to routers and read models

## Distinctions

- **AUTHENTICATION:** proves human identity (S1.5 frozen)
- **IDENTITY:** who is acting (`IdentityContext`)
- **ORGANIZATION:** SaaS tenant boundary (not sales `Company`)
- **MEMBERSHIP:** authority bridge with role
- **TENANT CONTEXT:** identity + org + membership (server-derived)
- **TENANT DATA ACCESS:** org-filtered queries
- **AUDIT PROVENANCE:** org stamp on AgentActionLog
