# REV-ORCH M4 — Calendar Tenant Credential Boundary

## Resolution: `calendar_executor.resolve_calendar_connector(organization_id)`

Uses `load_credentials(name, organization_id=org_id, allow_global_fallback=False)`.

Connectors tried in order: `google_calendar`, `outlook_calendar`.

## Prohibited
- Global credential fallback for tenant booking
- Client-supplied calendar_id as tenant authority
- AI credential selection
- Cross-tenant calendar reads

## Legacy Note
`runner_api_routers/integrations.py` direct calendar event routes exist but are NOT canonical M4 booking authority (LEGACY_CONTAINED / admin configure only).
