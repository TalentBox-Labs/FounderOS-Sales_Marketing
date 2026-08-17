# Canonical Tenant Contract v1.0

**Canonical Tenant:** `Organization`  
**Status:** FROZEN

## Resolution contract

```
authenticated human (IdentityContext)
  → active OrganizationMembership lookup
  → Organization record validation
  → TenantContext
```

## Server-derived authority

| Input source | Authority? |
|--------------|------------|
| Session JWT cookie | YES (identity) |
| `founder_os_organization` cookie | HINT ONLY — validated against membership |
| `POST /api/v1/tenant/select` body | HINT ONLY — validated against membership |
| Query `organization_id` | NO |
| Header `X-Organization-Id` | NO |
| Mutation JSON `organization_id` / `tenant_id` | NO |
| Form field `organization_id` | NO |

## Object ID validation

When client supplies `contact_id`, `deal_id`, `demand_id`, or `outcome_id`:

1. Resolve `TenantContext` from server identity + validated org hint
2. Lookup object with `organization_id + object_id` predicate
3. Mismatch → 404 (no cross-tenant leak)

## Legacy fallback

When `TenantContext` is `None` (no membership, DB unavailable, env-operator legacy):

- Bounded mutation guards skip org predicate
- Preserves S1.5 freeze compatibility for env-operator paths
- **Not** a cross-tenant bypass when session + membership exist

## Malicious attempt outcomes (verified)

| Attack | Expected |
|--------|----------|
| Org B cookie while member of A only | 403 |
| `tenant/select` with foreign org | 403 |
| Org B object ID under Org A context | 404 |
| Spoof org in mutation JSON body | Ignored; still 404 for foreign object |
