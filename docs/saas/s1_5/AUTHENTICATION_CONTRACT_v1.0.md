# AUTHENTICATION CONTRACT v1.0

**STATUS: FROZEN**  
**Sprint:** FOUNDER OS SaaS S1.5  
**App:** primary `runner_api`

## Method (v1-compatible)

```
valid human credentials (email + password)
        ↓
bcrypt verify against User.hashed_password
        ↓
HS256 JWT (python-jose) signed with SECRET_KEY
        ↓
httpOnly cookie founder_os_identity
        ↓
IdentityContext (HUMAN)
```

Future versioned evolution of token/session **implementation** is allowed if behavioral invariants remain.

## Behavioral contract

| Input | Result |
|-------|--------|
| Valid human credentials | Authenticated HUMAN IdentityContext |
| Invalid credentials | Rejected (401) |
| Rate-limited failures | 429 |
| Anonymous GET to protected Founder HTML (login required) | 303 → `/login` |
| Logout | Cookie cleared; `jti` denylisted in-process |

## Authentication MUST NOT rely on

- client `requested_by`
- client actor / display name headers
- `RUNNER_API_KEY` as human proof
- agent / service credentials as human proof

## Routes (frozen surface)

| Method | Path | Class |
|--------|------|-------|
| GET | `/login` | PUBLIC (login form) |
| POST | `/login` | PUBLIC (credential exchange) |
| POST | `/logout` | AUTHENTICATED_HUMAN (clears identity) |
| POST | `/api/v1/identity/login` | PUBLIC (JSON credential exchange) |
| POST | `/api/v1/identity/logout` | AUTHENTICATED_HUMAN / clears cookie |
| GET | `/api/v1/identity/me` | PUBLIC read of current IdentityContext |

**No** public `/register` on `runner_api`.

## Founder HTML protection

When `FOUNDER_OS_REQUIRE_LOGIN` is true (default outside pytest):

| Route | Class |
|-------|-------|
| GET `/cockpit` | AUTHENTICATED_HUMAN |
| GET `/operator` | AUTHENTICATED_HUMAN |
| GET `/operator/demand/register` | AUTHENTICATED_HUMAN |

Public Cloudflare Pages website remains **separate** and is not this app.

## Pytest compatibility

Unset `FOUNDER_OS_REQUIRE_LOGIN` + `PYTEST_CURRENT_TEST` → HTML gate off so frozen UI2.5 / OF1.5 / MDG1.5 GET suites remain 200 without session.
