# REV-ORCH M3.5 — Latest Assessment Isolation v1.0

## Status: FROZEN

## Endpoint

`GET /api/v1/revenue/contacts/{contact_id}/reply/latest-assessment`

## Tenant Isolation

1. `require_tenant_context(http_request)` extracts TenantContext from authenticated session
2. `inspect_latest_reply_assessment(db, tenant, contact_id)` calls
   `get_contact_for_tenant(db, org_id, contact_id)` which raises `TenantAccessError`
   if contact does not belong to session tenant
3. AgentActionLog query filters by `organization_id == tenant.organization_id`

## Blocked Vectors

| Attack | Mitigation |
|--------|-----------|
| Cross-tenant contact_id enumeration | get_contact_for_tenant rejects |
| Client organization_id override | Session-based tenant, not client-supplied |
| Direct AgentActionLog access | Filtered by org_id |

## Contract

```
LATEST_ASSESSMENT_TENANT_ISOLATION = PASS
CROSS_TENANT_ASSESSMENT_READ = BLOCKED
CLIENT_TENANT_SPOOFING = BLOCKED
```
