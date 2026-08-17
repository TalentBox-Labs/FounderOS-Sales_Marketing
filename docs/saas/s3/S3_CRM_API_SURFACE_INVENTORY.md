# S3 — CRM API Surface Inventory

**Routes audited:** 15  
**Prefix:** `/api/v1/crm`

| Route | Method | Entity | R/W | S3 status |
|-------|--------|--------|-----|-----------|
| `/contacts` | GET | Contact | Read | S3_READ_SCOPE |
| `/contacts/{id}` | GET | Contact | Read | S3_MUST_GUARD |
| `/contacts` | POST | Contact | Mutation | S3_MUST_GUARD |
| `/contacts/{id}/enrich` | POST | Contact | Mutation | S3_MUST_GUARD |
| `/contacts/{id}/score` | POST | Contact | Mutation | S3_MUST_GUARD |
| `/contacts/{id}/status` | PATCH | Contact | Mutation | S3_MUST_GUARD |
| `/deals` | GET | Deal | Read | S3_READ_SCOPE |
| `/deals/{id}` | GET | Deal | Read | S3_MUST_GUARD |
| `/deals` | POST | Deal | Mutation | S3_MUST_GUARD |
| `/deals/{id}/stage` | PATCH | Deal | Mutation | S3_MUST_GUARD |
| `/pipeline` | GET | Deal aggregate | Read | S3_READ_SCOPE |
| `/activities` | GET | Activity | Read | S3_READ_SCOPE |
| `/activities` | POST | Activity | Mutation | S3_MUST_GUARD |
| `/activities/{id}/complete` | POST | Activity | Mutation | S3_MUST_GUARD |
| `/followups` | GET | Mixed | Read | S3_READ_SCOPE |

**Company routes:** None (Company linked via Contact enrich only — not a separate list surface).

**Authentication:** `_verify_api_key` (Bearer optional when key unset).  
**TenantContext:** Resolved from human session + org cookie when present; legacy ID-only when absent (A3/A4 freeze compatibility).

**Ninth S2.5 risk:** MITIGATED — all live CRM mutation/read routes now tenant-scoped when TenantContext resolves.
