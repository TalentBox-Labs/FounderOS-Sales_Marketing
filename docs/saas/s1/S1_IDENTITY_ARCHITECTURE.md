# SaaS S1 — Identity Architecture

**Sprint:** FOUNDER OS SaaS S1  
**Date:** 2026-08-14  
**Status:** IMPLEMENTED  
**Primary app:** `runner_api` (`uvicorn runner_api:app`)

## Pattern

```
Authenticated Request
        ↓
Canonical Human User Identity  (User row + httpOnly JWT cookie)
        ↓
Role / Authority Context       (OWNER|ADMIN|MEMBER|VIEWER exposed; RBAC deferred)
        ↓
Trusted Request Context        (IdentityContext)
        ↓
Existing runner/domain APIs    (cockpit / operator / MDG proxies)
        ↓
Frozen Domain Contracts        (A3.5 / A4.5 / MC04.5 / MC06.5 / OF1.5 / MDG1.5)
```

Identity is an **outer wrapper**. Frozen services still receive `requested_by: str` from the server. Domain semantics are unchanged.

## Why this method

| Option | Verdict |
|--------|---------|
| Blind-copy `revenue_os.main` JWT Bearer | **NOT_SAFE** — collides with `RUNNER_API_KEY` Bearer; open `/auth/register` is public signup |
| Starlette `SessionMiddleware` | **NOT USED** — `itsdangerous` is not installed; would add a package |
| httpOnly JWT cookie + existing `python-jose` / bcrypt | **CHOSEN** — reuses installed crypto; Jinja-compatible; API-key Bearer remains service-only |

## Persistence decision

**REUSE_EXISTING_USER** (`revenue_os.models.user.User`).

| Question | Answer |
|----------|--------|
| Why persist? | Login must survive process restart; bootstrap OWNER is an instance operator, not a cookie fantasy |
| Schema | Existing `users` table: `id`, `email`, `hashed_password`, `full_name`, `role`, `is_active`, … |
| Tenant fields | **None added** |
| Migration | **NO** — table already created via `Base.metadata.create_all` |
| Blast radius | Identity module + Jinja login + Founder HTML GET gate + trusted-actor resolution |
| Rollback | Unset `FOUNDER_OS_REQUIRE_LOGIN`; stop issuing cookies; env operator fallback remains |
| Frozen contracts | Unchanged; wrappers inject `requested_by` |

## Request identity sources (priority)

1. `founder_os_identity` httpOnly cookie → HUMAN (after User lookup)
2. Else `Authorization: Bearer $RUNNER_API_KEY` → SERVICE (`is_human=False`)
3. Else ANONYMOUS
4. Founder UI mutation actor: session HUMAN, else legacy `FOUNDER_OS_OPERATOR_NAME`

`RUNNER_API_KEY` never becomes HUMAN.

## Jinja vs public website

| Surface | Auth |
|---------|------|
| `/cockpit`, `/operator`, `/operator/demand/register` | Login required when `FOUNDER_OS_REQUIRE_LOGIN` is true (default outside pytest) |
| Public Cloudflare Pages website | **Not** this app; not gated |
| Frozen CRM/QD/CO JSON APIs | Unchanged request schemas (client `requested_by` still present on those frozen routers) |
