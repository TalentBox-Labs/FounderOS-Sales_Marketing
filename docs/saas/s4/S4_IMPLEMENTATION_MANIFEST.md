# S4 — Implementation Manifest

## Modified
- `revenue_os/models/integrations.py` — org-scoped credentials + integration bindings
- `revenue_os/services/credentials_vault.py` — org-scoped load/save/delete
- `revenue_os/services/integration_tenant_resolution.py` — new
- `revenue_os/services/linkedin_enrichment.py` — org-scoped API key
- `runner_api_routers/integrations.py` — tenant-scoped connector CRUD
- `runner_api_routers/whatsapp.py` — tenant-scoped configure
- `runner_api_routers/n8n_webhooks.py` — tenant binding + scoped contacts
- `runner_api_routers/crm.py` — pass org_id to enrich
- `runner_api.py` — connector_credentials migration patch
- `revenue_os/models/__init__.py`

## New
- `tests/test_saas_s4_integration_tenant_isolation.py`
- `docs/saas/s4/*`

## Database migrations
1 (startup patch + create_all for bindings table)

## Frozen contract changes
0
