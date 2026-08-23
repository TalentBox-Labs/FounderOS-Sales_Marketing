# S4.5 — Connector Migration Attestation

## S4 migration (verified in `runner_api.py`)

**Function:** `_migrate_connector_credentials_tenant`  
**Type:** Startup additive rebuild (idempotent when `id` + `organization_id` exist)

### Behavior

1. Detect legacy schema (missing `id` or `organization_id`)
2. Read existing rows (connector_name, category, encrypted_config, updated_at)
3. Drop and recreate table from current model
4. Re-insert with `organization_id=NULL` (GLOBAL_BY_DESIGN)
5. Encrypted configs preserved — no secret loss

### Idempotency

Second startup: columns present → no-op.

### S4.5

**Database Migrations: 0** (freeze sprint adds none)  
**Runtime Changes: 0** (S4 patch preserved, not modified)

### Rollback

Manual restore from backup if rebuild fails mid-flight; no Alembic downgrade defined.
