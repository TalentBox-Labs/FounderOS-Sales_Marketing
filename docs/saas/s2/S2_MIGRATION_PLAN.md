# SaaS S2 — Migration Plan

## New tables

- `organizations`
- `organization_memberships`

Created via `Base.metadata.create_all()` on startup.

## Additive columns

| Table | Column | Nullable |
|-------|--------|----------|
| `contacts` | `organization_id` | YES |
| `deals` | `organization_id` | YES |
| `agent_action_log` | `organization_id` | YES |

Applied via `_migrate_missing_columns()` in `runner_api.py` (additive-only).

## Bootstrap

1. `bootstrap_owner_if_needed()` (S1, unchanged)
2. `bootstrap_tenant_if_needed()` — org + OWNER memberships + backfill null org IDs

## Idempotency

- Org creation skipped if any organization exists
- Users without membership get OWNER on existing default org
- Backfill only touches null `organization_id`

## Rollback

Drop columns/tables manually; no destructive migration in S2.

## Failure handling

Bootstrap exceptions logged; startup continues (non-blocking).
