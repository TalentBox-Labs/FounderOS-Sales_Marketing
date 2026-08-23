# AUTH COOKIE / TOKEN SECURITY ATTESTATION

**Sprint:** FOUNDER OS SaaS S1.5  
**Date:** 2026-08-15  
**Cookie:** `founder_os_identity`  
**Evidence:** `runner_api_routers/identity.py`, `revenue_os/auth.py`, `revenue_os/config.py`

## Classification matrix

| Control | Classification | Evidence |
|---------|----------------|----------|
| HttpOnly | **PASS** | `_set_identity_cookie(..., httponly=True)` |
| Secure (production) | **PARTIAL** | Opt-in via `FOUNDER_OS_COOKIE_SECURE`; default false for local HTTP |
| SameSite | **PASS** | `samesite="lax"` |
| Expiration | **PASS** | JWT `exp` + cookie `max_age` from `ACCESS_TOKEN_EXPIRE_MINUTES` |
| Signature algorithm | **PASS** | HS256 (`python-jose`) |
| Secret / key source | **PASS** | `settings.SECRET_KEY` (required; empty / `change-me` fatal) |
| Token subject / user binding | **PASS** | `sub` → DB `User` reload; cookie `name` not authoritative for humans |
| Invalid token rejection | **PASS** | `JWTError` → no session |
| Expired token rejection | **PASS** | jose decode enforces `exp` |
| Logout behavior | **PARTIAL** | Cookie deleted + in-process `_revoked_jtis`; not shared across workers |
| Token replay implications | **PARTIAL** | Valid until expiry/logout; stolen cookie usable until then |
| CSRF implications | **PARTIAL** | SameSite=Lax mitigates cross-site cookie POSTs; no CSRF token |

## Overall JWT / Cookie Security

**PARTIAL**

Non-critical / documented limitations:

1. `Secure` must be enabled in HTTPS production (`FOUNDER_OS_COOKIE_SECURE=true`)
2. Logout denylist is process-local
3. No CSRF synchronizer token (see CSRF section below)

No serious defect found that requires STOP / architecture redesign for freeze.

## CSRF Protection

**PARTIAL** — non-blocking for freeze with strong SameSite evidence.

| Mutation surface | Auth | CSRF control observed |
|------------------|------|------------------------|
| MDG manual demand POST | Cookie session and/or API key + trusted human | SameSite=Lax |
| Cockpit / Operator POSTs | Same | SameSite=Lax |
| Frozen CRM / QD / CO JSON | Bearer API key + `requested_by` (frozen schemas) | API-key gated; not cookie-primary |
| Editorial / Publishing (Jinja shell) | Mixed / legacy | Not newly cookie-gated in S1 |

**No** CSRF middleware token / Origin enforcement found on cookie mutations.

**Why freeze is still allowed:** SameSite=Lax prevents modern browsers from attaching the identity cookie on cross-site POST. Residual risk is documented for a future hardening sprint (CSRF token or Origin checks), **not** an S1.5 identity architecture change.

## Production checklist (ops)

- Set strong `SECRET_KEY`
- Set `FOUNDER_OS_COOKIE_SECURE=true` behind HTTPS
- Prefer `FOUNDER_OS_REQUIRE_LOGIN=true`
- Rotate Owner password independently of `RUNNER_API_KEY`
