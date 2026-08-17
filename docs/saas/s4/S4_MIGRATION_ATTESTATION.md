# S4 — Migration Attestation

**Database migration:** YES (additive startup patch)

**Change:** `connector_credentials` rebuilt with `id` PK + nullable `organization_id` + unique `(organization_id, connector_name)`.

**Legacy rows:** Migrated with `organization_id=NULL` (GLOBAL_BY_DESIGN).

**New table:** `organization_integration_bindings` via `create_all`.

No destructive data loss; encrypted configs preserved.
