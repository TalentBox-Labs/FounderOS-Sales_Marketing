# S4 — Webhook Tenant Binding Contract

**Route:** `POST /webhooks/n8n/{event_name}` — TENANT_BOUND when secret resolves org.

**Org resolution order:**
1. `OrganizationIntegrationBinding` by `X-N8N-Secret`
2. Env pair `N8N_INBOUND_SECRET` + `N8N_INBOUND_ORGANIZATION_ID`
3. Legacy: no org binding → ID-only contact lookup (dev/API-key-only)

**Never trusted:** payload `organization_id`, `tenant_id`, `contact_id` for org authority.
