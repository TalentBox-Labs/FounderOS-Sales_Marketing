# S3.5 — CRM Route Baseline v1.0

**Source:** `runner_api_routers/crm.py` (repository inspection)  
**Prefix:** `/api/v1/crm`  
**Live route count:** 15  
**Dormant routes:** 0

## Read routes (7)

| # | Method | Path | Entity | Tenant guard | Lookup | Status |
|---|--------|------|--------|--------------|--------|--------|
| 1 | GET | `/contacts` | Contact | `resolve_crm_tenant_read` + `apply_contact_org_filter` | org-scoped list | LIVE |
| 2 | GET | `/contacts/{contact_id}` | Contact | `scoped_contact` | org + id | LIVE |
| 3 | GET | `/deals` | Deal | `apply_deal_org_filter` | org-scoped list | LIVE |
| 4 | GET | `/deals/{deal_id}` | Deal | `scoped_deal` | org + id | LIVE |
| 5 | GET | `/pipeline` | Deal aggregate | `get_pipeline_health(organization_id=...)` | org-scoped count | LIVE |
| 6 | GET | `/activities` | Activity | `scoped_contact`/`scoped_deal` + `verify_activity_in_tenant` | via linked entity | LIVE |
| 7 | GET | `/followups` | Mixed | `get_followups(organization_id=...)` | org-scoped | LIVE |

## Mutation routes (8)

| # | Method | Path | Entity | Tenant guard | Domain op | Status |
|---|--------|------|--------|--------------|-----------|--------|
| 1 | POST | `/contacts` | Contact | `optional_tenant_mutation` + `stamp_new_contact_org` | create | LIVE |
| 2 | POST | `/contacts/{contact_id}/enrich` | Contact | `scoped_contact` | Proxycurl enrich | LIVE |
| 3 | POST | `/contacts/{contact_id}/score` | Contact | `scoped_contact` | A4 score | LIVE |
| 4 | PATCH | `/contacts/{contact_id}/status` | Contact | `scoped_contact` + HUMAN_ONLY | A4.5 status | LIVE |
| 5 | POST | `/deals` | Deal | `scoped_contact` + `assign_new_deal_org` | create | LIVE |
| 6 | PATCH | `/deals/{deal_id}/stage` | Deal | `scoped_deal` + HUMAN_ONLY | A3.5 stage | LIVE |
| 7 | POST | `/activities` | Activity | `scoped_contact`/`scoped_deal` | create | LIVE |
| 8 | POST | `/activities/{activity_id}/complete` | Activity | `verify_activity_in_tenant` | complete | LIVE |

## Auth

All routes: `_verify_api_key` (Bearer when key configured).  
Human session + org cookie → TenantContext enforced.  
No session → legacy ID-only fallback (A3/A4 freeze compatibility).

## Company routes

**None** — Company is mutated only as side-effect of contact enrich (not a list/read API surface).
