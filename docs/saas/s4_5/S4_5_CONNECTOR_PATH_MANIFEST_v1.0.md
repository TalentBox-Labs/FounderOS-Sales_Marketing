# S4.5 — Connector Path Manifest v1.0

**Total paths reconciled:** 14  
**Tenant-scoped:** 10  
**Global-by-design:** 4

## Tenant-scoped (10)

| # | Path | Trigger | Org resolution |
|---|------|---------|----------------|
| 1 | `load_credentials(org, fallback=False)` | CRM enrich, tenant API | TenantContext |
| 2 | `save_credentials(org)` | configure_connector | `_integration_org_id()` |
| 3 | `delete_credentials(org)` | remove_connector | `_integration_org_id()` |
| 4 | `list_configured_connectors(org)` | list_connectors | `_integration_org_id()` |
| 5 | integrations `/email/configure` | POST | session org |
| 6 | integrations `/slack/configure` | POST | session org |
| 7 | integrations `/google-calendar/configure` | POST | session org |
| 8 | integrations `/outlook-calendar/configure` | POST | session org |
| 9 | whatsapp `/configure` | POST | `resolve_integration_org_id()` |
| 10 | `linkedin_enrichment._api_key(org)` | CRM enrich | contact tenant org |

## Global-by-design (4)

| # | Path | Reason |
|---|------|--------|
| 1 | `hydrate_all_connectors()` | Process startup; NULL-org only |
| 2 | CONNECTOR_CATALOG `source=env` | Deploy-time env vars |
| 3 | save/load with `org=None` | Legacy API-key-only no session |
| 4 | `gmail_sync._vault_config()` | Loads NULL-org row; OAuth callback GLOBAL_BY_DESIGN |

## Webhook routes (2)

| Route | Classification |
|-------|----------------|
| `POST /webhooks/n8n/{event_name}` | TENANT_BOUND when secret resolves org |
| `GET /webhooks/n8n/catalog` | GLOBAL_BY_DESIGN (reference doc) |

**Unsafe-unscoped live routes:** 0
