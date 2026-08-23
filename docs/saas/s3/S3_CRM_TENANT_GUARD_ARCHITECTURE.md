# S3 — CRM Tenant Guard Architecture

Reuses S2/S2.5 abstractions — no parallel framework.

```
TenantContext (resolve_crm_tenant_read / optional_tenant_mutation)
    ↓
tenant_scoped_access (apply_*_org_filter, scoped lookups)
    ↓
tenant_mutation_guard (scoped_contact, scoped_deal, assign_new_deal_org)
    ↓
existing frozen domain ops (A3.5, A4.5, score_contact, etc.)
```

## Read path

`resolve_crm_tenant_read()` → allows VIEWER → org filters on queries.

## Mutation path

`optional_tenant_mutation()` → blocks VIEWER → `scoped_contact` / `scoped_deal` before domain call.

## Legacy fallback

When no human session/membership: tenant is `None` → pre-S3 ID-only behavior preserved for A3/A4 freeze tests.

## New helpers (S3)

- `apply_contact_org_filter`, `apply_deal_org_filter` in `tenant_scoped_access.py`
- `resolve_crm_tenant_read`, `crm_tenant_org_id` in `tenant_mutation_guard.py`
- `verify_activity_in_tenant` for Activity scoping via linked Contact/Deal
- Optional `organization_id` on `get_pipeline_health`, `get_followups`, `get_deals_at_risk`
