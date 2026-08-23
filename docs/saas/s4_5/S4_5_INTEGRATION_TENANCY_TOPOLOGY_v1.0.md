# S4.5 — Integration Tenancy Topology v1.0

## Outbound (tenant-owned)

```
Human Session → TenantContext → organization_id
    → credentials_vault.load/save/delete(organization_id=...)
    → External connector client
```

## Inbound (n8n)

```
X-N8N-Secret → OrganizationIntegrationBinding (or env pair)
    → organization_id
    → build_integration_tenant_context (SERVICE, not human)
    → scoped_contact / tenant guards
    → frozen domain side effect
```

## Models (verified in repo)

| Model | Table | Key fields |
|-------|-------|------------|
| `ConnectorCredentialRecord` | `connector_credentials` | `id`, `organization_id` (nullable), `connector_name`, unique `(organization_id, connector_name)` |
| `OrganizationIntegrationBinding` | `organization_integration_bindings` | `organization_id`, `integration_name`, `inbound_secret` (unique) |

## Services

- `revenue_os/services/credentials_vault.py`
- `revenue_os/services/integration_tenant_resolution.py`
- `runner_api_routers/n8n_webhooks.py`
- `runner_api_routers/integrations.py`
