# CRM Read Isolation Contract v1.0

**Frozen:** 7/7 read routes  
**Architecture:** SERVER TENANT SCOPE ∩ CLIENT FILTER

## Contract rules

1. Server applies organization filter **before** client-supplied search/status/stage filters.
2. Client filter params never determine tenant authority.
3. Individual GET by ID uses `scoped_contact` / `scoped_deal` — cross-tenant → 404.
4. Aggregates (`/pipeline`, `/followups`) pass `organization_id` to service layer.
5. Activities without direct `organization_id` scoped via linked Contact/Deal.

## Route → scope mapping

| Route | Server scope | Client filter (after scope) |
|-------|--------------|----------------------------|
| GET `/contacts` | `apply_contact_org_filter` | status, search, limit |
| GET `/contacts/{id}` | `scoped_contact` | — |
| GET `/deals` | `apply_deal_org_filter` | stage, limit |
| GET `/deals/{id}` | `scoped_deal` | — |
| GET `/pipeline` | `get_pipeline_health(org_id)` | — |
| GET `/activities` | `verify_activity_in_tenant` | contact_id, deal_id (validated first) |
| GET `/followups` | `get_followups(org_id)` | — |

## Anti-pattern (blocked)

```
CLIENT FILTER = TENANT AUTHORITY   ❌
```

## Verified behaviors

- List isolation: org A never sees org B contacts/deals
- Search isolation: search param applied after org filter
- Summary/count: pipeline `total_deals` org-scoped
