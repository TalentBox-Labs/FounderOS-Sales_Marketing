# FOUNDER OS IDENTITY FOUNDATION BASELINE v1.0

**STATUS: FROZEN**  
**Sprint:** FOUNDER OS SaaS S1.5  
**Date:** 2026-08-15  
**Implementation sprint:** FOUNDER OS SaaS S1  
**Primary app:** `runner_api` (`uvicorn runner_api:app`)

## Freeze scope

This baseline freezes the **outer identity / authentication wrapper** on the primary Founder OS application. It does **not** freeze tenancy, organization membership, or broad RBAC enforcement.

## Frozen invariants

| # | Invariant |
|---|-----------|
| 1 | Canonical human identity is a persisted `User` row |
| 2 | Primary authentication is bcrypt password → httpOnly JWT cookie `founder_os_identity` |
| 3 | Trusted human actor for Founder UI proxies is server-derived (`IdentityContext` or legacy env) |
| 4 | Client `requested_by` is never trusted authority on wrapped Founder proxies |
| 5 | `RUNNER_API_KEY` is SERVICE / LEGACY_INTERNAL — never HUMAN |
| 6 | HUMAN / SERVICE / AGENT / AI remain distinct principal kinds |
| 7 | Anonymous access to Founder HTML surfaces is blocked when login is required |
| 8 | Role vocabulary is OWNER / ADMIN / MEMBER / VIEWER; enforcement deferred |
| 9 | No `tenant_id` / `organization_id` / `workspace_id` on identity or domain models |
| 10 | Frozen business contracts remain outer-wrapped, not rewritten |

## Request model (frozen)

```
Authenticated Request
        ↓
Canonical Human User Identity
        ↓
Role vocabulary (not enforced)
        ↓
IdentityContext
        ↓
Authority adapter (_trusted_cockpit_operator / resolve_trusted_human)
        ↓
Frozen Domain Operation
```

## Explicitly NOT frozen

- Organization / Workspace models
- TenantContext
- Tenant-scoped queries
- Broad endpoint RBAC
- Public signup
- OAuth / IdP
- Multi-worker logout denylist productization
- Full CSRF token suite (SameSite=Lax attested as current control)

## Parents (UNCHANGED)

A1.5 · A3.5 · A4.5 · MC04.5 · MC06.5 · UI2.5 · OF1.5 · MDG1.5 · UI1.1 HUMAN_ONLY gate

## Amendment rule

Changes to this baseline require ADR + approved sprint. Do not silently evolve cookie/auth architecture under freeze without a versioned extension.
