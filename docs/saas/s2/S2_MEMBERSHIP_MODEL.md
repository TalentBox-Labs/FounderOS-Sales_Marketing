# SaaS S2 — Membership Model

**Bridge:** `IdentityContext` → `OrganizationMembership` → `TenantContext`

## Model

| Field | Type | Notes |
|-------|------|-------|
| `user_id` | FK → `users.id` | Canonical human user |
| `organization_id` | FK → `organizations.id` | Tenant |
| `role` | string | Frozen S1.5 vocabulary |
| `status` | enum | `active` \| `disabled` |

**Unique constraint:** `(user_id, organization_id)`

## Roles (frozen S1.5)

`OWNER` / `ADMIN` / `MEMBER` / `VIEWER`

S2 enforces mutation blocking for `VIEWER` on bounded Founder UI mutation proxies.
