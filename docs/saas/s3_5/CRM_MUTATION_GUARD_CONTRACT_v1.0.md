# CRM Mutation Guard Contract v1.0

**Frozen:** 8/8 mutation routes  
**Pattern:** `optional_tenant_mutation()` → ownership verify → frozen domain function

## Contract rules

1. **TenantContext required** when human session resolves (VIEWER blocked at guard).
2. **Organization ownership verified** before domain invocation — object ID alone insufficient.
3. **Cross-tenant mutation** returns 404 (non-leaking).
4. **Role enforcement** layered: VIEWER → 403; MEMBER/ADMIN/OWNER per S2.5 vocabulary.
5. **requested_by server binding preserved** on A3/A4 routes via `is_human_approver`.
6. **Frozen domain functions unchanged:** `apply_contact_status_update`, `apply_deal_stage_update`, `score_contact`.

## Route → guard mapping

| Route | Guard | Ownership check |
|-------|-------|-----------------|
| POST `/contacts` | `optional_tenant_mutation` | email dup check org-scoped; `stamp_new_contact_org` |
| POST `/contacts/{id}/enrich` | `optional_tenant_mutation` | `scoped_contact` |
| POST `/contacts/{id}/score` | `resolve_crm_tenant_read` + `scoped_contact` | org + contact_id |
| PATCH `/contacts/{id}/status` | `optional_tenant_mutation` | `scoped_contact` |
| POST `/deals` | `optional_tenant_mutation` | `scoped_contact` if contact_id; `assign_new_deal_org` |
| PATCH `/deals/{id}/stage` | `optional_tenant_mutation` | `scoped_deal` |
| POST `/activities` | `optional_tenant_mutation` | `scoped_contact` / `scoped_deal` |
| POST `/activities/{id}/complete` | `optional_tenant_mutation` | `verify_activity_in_tenant` |

## Legacy fallback

When `optional_tenant_mutation()` returns `None` (no tenant): pre-S3 ID-only behavior for API-key-only A3/A4 tests.
