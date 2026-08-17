# S2.5 — Residual Tenancy Risk Register v1.0

**Status:** FROZEN (register only — no fixes in S2.5)

## S2-identified residuals (verified)

### 1. Ungated CRM API ID-only mutations

| Attribute | Value |
|-----------|-------|
| Location | `runner_api_routers/crm.py` — `/api/v1/crm/*` |
| Auth | `_verify_api_key` only — no tenant resolution |
| Severity | **CRITICAL** |
| Classification | **S3_REQUIRED** |
| Evidence | No `optional_tenant_mutation`, `scoped_contact`, or org filters in module |

Affected mutations: contact enrich/create/score/status, deal create/stage, activity create/complete.  
Affected reads: list/get contacts, deals, activities — global queries.

### 2. Global connector credentials

| Attribute | Value |
|-----------|-------|
| Location | `revenue_os/services/credentials_vault.py`, `ConnectorCredentialRecord` |
| Scope | Global by PK `connector_name` — no `organization_id` |
| Severity | **HIGH** |
| Classification | **FUTURE_SECURITY** |
| Evidence | `S2_SECRET_ISOLATION_FUTURE_BOUNDARY.md` |

## Additional residuals discovered

| # | Risk | Severity | Classification |
|---|------|----------|----------------|
| 3 | Editorial/publishing read surfaces unscoped | MEDIUM | S3_REQUIRED |
| 4 | Legacy env-operator path skips tenant when no membership | LOW | GLOBAL_BY_DESIGN (single-founder compat) |
| 5 | Multi-org user requires explicit org select (no UI switcher) | LOW | S3_REQUIRED |
| 6 | Pipeline global shared reference | LOW | GLOBAL_BY_DESIGN |
| 7 | Background heartbeat/scheduler global | LOW | GLOBAL_BY_DESIGN |
| 8 | Webhook handlers (n8n) — not tenant-scoped in S2 | MEDIUM | S3_REQUIRED |

## False positives

- `Company` model — sales CRM entity, not SaaS tenant (by design)
- `User` without `organization_id` — identity is global; membership bridges to org

## Count

**Additional residual items beyond S2 report:** 6  
**Total documented:** 8
