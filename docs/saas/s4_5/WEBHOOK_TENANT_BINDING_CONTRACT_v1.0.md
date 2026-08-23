# Webhook Tenant Binding Contract v1.0

**Route:** `POST /webhooks/n8n/{event_name}`

## Trusted org resolution (in order)

1. `OrganizationIntegrationBinding.inbound_secret` == `X-N8N-Secret`
2. Env: `N8N_INBOUND_SECRET` + `N8N_INBOUND_ORGANIZATION_ID` match secret

## Never trusted for org authority

- `contact_id`, `deal_id`, `company_id`
- Payload `organization_id`, `tenant_id`
- `requested_by`, role, human metadata

## Object resolution

After org resolves → `build_integration_tenant_context` → `scoped_contact` → 404 on mismatch.

## Legacy

No binding + no secret → ID-only lookup (GLOBAL_BY_DESIGN dev path); documented LOW risk.
