# S4 — Connector Credential Resolution Contract

`load_credentials(connector_name, organization_id=..., allow_global_fallback=False)`

1. When `organization_id` set: query exact org row only.
2. When `organization_id` is None: query NULL-org legacy row only.
3. `connector_name` alone is never sufficient for tenant-scoped resolution.
4. Integration CRUD routes pass `_integration_org_id()` from session/cookie.
