# REV-ORCH M3.5 — Tenant Resolution Attestation v1.0

## Status: FROZEN

## Trusted Tenant Source

`OrganizationIntegrationBinding` resolved via `resolve_n8n_organization_id(x_n8n_secret=...)`.

## Resolution Path

1. `X-N8N-Secret` header → `resolve_n8n_organization_id()` → `organization_id`
2. Contact resolved via `_resolve_scoped_contact(db, contact_id, organization_id=org_id)`
3. `scoped_contact()` enforces `Contact.organization_id == resolved_org`
4. Email fallback: `_resolve_contact_by_email(db, organization_id, email)` — scoped to org

## Blocked Attack Vectors

| Vector | Mitigation | Test |
|--------|-----------|------|
| Payload `organization_id` override | Ignored; binding determines tenant | test_payload_tenant_spoof_blocked |
| Cross-tenant contact_id | scoped_contact rejects | test_cross_tenant_contact_id_blocked |
| Cross-tenant email resolution | Filtered by organization_id | test_cross_tenant_email_resolution_blocked |
| No binding present | M3 workflow not invoked | Code path: `if organization_id is not None` |

## Contract

```
INBOUND_TENANT_RESOLUTION = INTEGRATION_BINDING_ONLY
CLIENT_PAYLOAD_TENANT_AUTHORITY = PROHIBITED
CROSS_TENANT_REPLY_INJECTION = BLOCKED
```
