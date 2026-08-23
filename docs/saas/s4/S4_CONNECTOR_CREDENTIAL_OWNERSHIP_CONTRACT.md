# S4 — Connector Credential Ownership Contract

**Owner:** Organization (via nullable `organization_id` on `connector_credentials`)

| organization_id | Classification |
|-----------------|----------------|
| UUID | Tenant-owned credential |
| NULL | GLOBAL_BY_DESIGN legacy/system |

Tenant-owned operations MUST NOT use NULL-org credentials unless `allow_global_fallback=False` (default).
