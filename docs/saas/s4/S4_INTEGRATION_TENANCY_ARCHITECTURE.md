# S4 — Integration Tenancy Architecture

## Outbound
```
Identity → TenantContext → Organization → org-scoped ConnectorCredential → External API
```

## Inbound
```
Webhook → X-N8N-Secret binding → Organization → TenantContext (service) → scoped object → domain op
```

Payload object IDs never establish tenant authority.

## Models
- `ConnectorCredentialRecord`: `(organization_id, connector_name)` unique; NULL org = GLOBAL_BY_DESIGN legacy
- `OrganizationIntegrationBinding`: trusted inbound secret → organization
