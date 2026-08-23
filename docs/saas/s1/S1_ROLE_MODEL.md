# SaaS S1 — MVP Role Model

**Sprint:** FOUNDER OS SaaS S1  
**Enforcement:** **DEFERRED_TO_S2** (except HUMAN_ONLY, which remains)

## Roles

| Role | Semantics |
|------|-----------|
| OWNER | Bootstrap instance human; future tenant owner |
| ADMIN | Privileged operator |
| MEMBER | Default `User.role` on the existing model |
| VIEWER | Read-intended; not yet denied mutations by role |

Stored on `User.role` (string, already existed). Normalized in IdentityContext.

## What S1 does

- Persist / expose role on login and `/api/v1/identity/me`
- Bootstrap user is `owner`
- Keep UI1.1 / editorial `is_human_approver` as the mutation gate

## What S1 does not do

- Endpoint RBAC matrices
- Tenant membership
- VIEWER-only read enforcement

S2 should attach role to Organization membership, then enforce.
