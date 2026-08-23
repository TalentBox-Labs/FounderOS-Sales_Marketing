# Connector Credential Ownership Contract v1.0

**Canonical ownership:** Organization → ConnectorCredentialRecord

## Classifications

| organization_id | Classification |
|-----------------|----------------|
| Valid UUID | **TENANT_OWNED** |
| NULL | **GLOBAL_BY_DESIGN** (legacy/system) |

## Prohibited authority sources for tenant-owned execution

- `connector_name` alone
- Client-supplied `organization_id` / `tenant_id`
- Business object ID (`contact_id`, `deal_id`)
- Payload `requested_by`
- Arbitrary HTTP headers (except trusted integration secret binding for inbound)

## Resolution

Tenant-owned execution MUST pass `organization_id` from server-derived TenantContext or trusted integration binding.
