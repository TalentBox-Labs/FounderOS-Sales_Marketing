# Organization + Membership Contract v1.0

**Status:** FROZEN

## Organization

| Field | Constraint |
|-------|------------|
| `id` | UUID PK |
| `name` | required |
| `slug` | unique, indexed |
| `status` | `active` \| `suspended` |

**Not included:** billing, subscriptions, workspaces, seats, CRM semantics.

## Membership

| Field | Constraint |
|-------|------------|
| `user_id` | FK → users |
| `organization_id` | FK → organizations |
| `role` | OWNER / ADMIN / MEMBER / VIEWER |
| `status` | `active` \| `disabled` |

**Unique:** `(user_id, organization_id)`

## Role vocabulary (frozen S1.5)

| Role | Mutations (S2 bounded slice) |
|------|------------------------------|
| OWNER | allowed |
| ADMIN | allowed |
| MEMBER | allowed |
| VIEWER | **blocked** (403) |

## Bootstrap

- Trigger: startup `bootstrap_tenant_if_needed()` after identity bootstrap
- Idempotent: skips org creation if any org exists; adds missing memberships
- Existing users → OWNER on default org
- Backfill: null `organization_id` on Contact, Deal, AgentActionLog

## Prohibitions

- No anonymous organization resolution
- No membership spoofing via request metadata
- No invitation UX in S2/S2.5
- No billing roles
