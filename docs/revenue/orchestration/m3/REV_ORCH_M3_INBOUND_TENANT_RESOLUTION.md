# REV-ORCH M3 — Inbound Tenant Resolution

Trusted source: `OrganizationIntegrationBinding` via `X-N8N-Secret` → `resolve_n8n_organization_id`.

- Payload `organization_id` / `tenant_id` ignored.
- `contact_id` is an object hint, validated with `scoped_contact` / `get_contact_for_tenant`.
- Optional email lookup is tenant-scoped and requires exactly one match; otherwise unmatched (no CRM mutation).
- Cross-tenant contact_id → HTTP 404.
- M3 analysis runs only when organization_id is resolved from binding.
