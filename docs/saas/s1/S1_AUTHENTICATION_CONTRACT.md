# SaaS S1 — Authentication Contract

**Sprint:** FOUNDER OS SaaS S1  
**App:** primary `runner_api`

## Method

**Password login (bcrypt) → signed JWT in httpOnly cookie `founder_os_identity`.**

Reuse: `revenue_os.auth.hash_password` / `verify_password` / `create_access_token` (`python-jose` HS256, `SECRET_KEY`).

## Routes

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/login` | Jinja login form |
| POST | `/login` | Form or JSON credentials |
| POST | `/logout` | Revoke `jti`, delete cookie |
| POST | `/api/v1/identity/login` | JSON login |
| POST | `/api/v1/identity/logout` | JSON logout |
| GET | `/api/v1/identity/me` | Public IdentityContext |

**No** `/register` on `runner_api`. Public signup is out of scope.

## Cookie

| Flag | Value |
|------|-------|
| HttpOnly | yes |
| SameSite | Lax |
| Secure | `FOUNDER_OS_COOKIE_SECURE` (off for local HTTP) |
| Path | `/` |
| Max-Age | `ACCESS_TOKEN_EXPIRE_MINUTES` (default 1440) |

JWT claims: `sub`, `email`, `name`, `role`, `kind=HUMAN`, `amr=password`, `jti`, `iss=founder_os_runner_api`, `exp`.

Human sessions **must** re-load `User` by `sub`. Cookie `name` is not trusted over the database.

Logout adds `jti` to an in-process denylist (single-worker). Multi-worker revocation is S2+.

## HTML gate

`FOUNDER_OS_REQUIRE_LOGIN`:

- `true`/`1` → anonymous GET `/cockpit`, `/operator`, `/operator/demand/register` → **303 `/login`**
- unset + `PYTEST_CURRENT_TEST` → **false** (preserves UI2.5 / OF1.5 / MDG1.5 GET 200)
- unset in production → **true**

## Security controls (MVP)

- bcrypt hashing
- Invalid credentials → 401
- Brute-force: per-email failure window → 429 (`FOUNDER_OS_LOGIN_MAX_FAILURES`, default 8 / 15 min)
- Open-redirect blocked (`next` must be a relative path)
- Login HTML does not render secrets
- CSRF: SameSite=Lax on the identity cookie; login has no prior session cookie
- Bearer `RUNNER_API_KEY` is not a session

## Why not JWT in Authorization for humans

`_verify_api_key` treats Bearer as the shared service secret. Putting a user JWT in the same slot would 401 or, worse, confuse human vs service. Humans use the cookie. Services keep the API key.
