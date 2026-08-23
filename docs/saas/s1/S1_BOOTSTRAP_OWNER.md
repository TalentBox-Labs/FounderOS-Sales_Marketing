# SaaS S1 — Bootstrap Owner

**Sprint:** FOUNDER OS SaaS S1

## Why

The hosted single-user instance must remain operable after identity persistence. There is no public signup on `runner_api`.

## Mechanism

On `runner_api` startup, `bootstrap_owner_if_needed()`:

1. Reads `FOUNDER_OS_BOOTSTRAP_EMAIL` + `FOUNDER_OS_BOOTSTRAP_PASSWORD`
2. Display name from `FOUNDER_OS_BOOTSTRAP_NAME` or `FOUNDER_OS_OPERATOR_NAME`
3. Aborts if the name fails `is_human_approver`
4. Creates `User(role=owner)` **only if that email is absent**
5. Logs the email, **never the password**

If env vars are unset, no user is created (tests / freeze suites keep working via env operator fallback).

## Local setup

```bash
# .env — never commit real values
SECRET_KEY=<urlsafe-32>
FOUNDER_OS_BOOTSTRAP_EMAIL=you@example.com
FOUNDER_OS_BOOTSTRAP_PASSWORD=<strong>
FOUNDER_OS_BOOTSTRAP_NAME=Krishna Founder
FOUNDER_OS_REQUIRE_LOGIN=true
FOUNDER_OS_OPERATOR_NAME=Krishna Founder   # legacy fallback during transition
```

Restart `uvicorn runner_api:app`, then open `/login`.

## Rotation / recovery

- Change password in the `users` row (hashed via `revenue_os.auth.hash_password`) or create a new Owner email and deactivate the old row (`is_active=0`)
- Lost session: cookies expire; logout revokes `jti` in-process
- Lost Owner password: operator with DB access re-hashes; no hardcoded Founder account in git

## Credentials committed

**0.** `.env.example` contains comments only.
