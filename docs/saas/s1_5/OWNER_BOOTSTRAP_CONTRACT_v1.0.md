# OWNER BOOTSTRAP CONTRACT v1.0

**STATUS: FROZEN**  
**Sprint:** FOUNDER OS SaaS S1.5  
**Function:** `runner_api_routers.identity.bootstrap_owner_if_needed`  
**Hook:** `runner_api` startup

## Behavior

1. Requires `FOUNDER_OS_BOOTSTRAP_EMAIL` + `FOUNDER_OS_BOOTSTRAP_PASSWORD`
2. Name from `FOUNDER_OS_BOOTSTRAP_NAME` or `FOUNDER_OS_OPERATOR_NAME`
3. Aborts if name fails `is_human_approver`
4. Creates `User(role=owner)` **only if email absent**
5. Logs email; **never** logs password
6. If env unset → no-op (legacy env operator still works for freeze suites)

## Safety attestations

| Check | Result |
|-------|--------|
| Hardcoded production password in repo | **NONE** |
| Credentials committed | **0** (`.env.example` comments only) |
| Silent overwrite of existing user | **NO** — early return if email exists |
| Public signup | **ABSENT** on runner_api |

## Limitations (documented, not defects for freeze)

- No self-service password reset UI
- Recovery requires DB access + re-hash via `hash_password`
- Bootstrap is instance-scoped, not multi-tenant

## Continuity

Existing single-Founder instances remain operable via:

1. Bootstrap OWNER then login, and/or
2. Legacy `FOUNDER_OS_OPERATOR_NAME` for Founder UI proxy mutations during transition
