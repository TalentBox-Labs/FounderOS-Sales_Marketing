# SaaS S2 — Tenant Resolution

**Module:** `revenue_os/services/tenant_resolution.py`

## Resolution order

1. Authenticated human `IdentityContext` (session cookie)
2. Organization hint: cookie `founder_os_organization` or explicit API hint
3. Membership validation against hint
4. Single active membership → auto-select when no hint

## Rejection rules

| Condition | Result |
|-----------|--------|
| Unknown organization | 403 |
| Non-member organization | 403 |
| Disabled membership | 403 |
| Multiple memberships, no hint | 403 |

## API

- `GET /api/v1/tenant/me` — current resolved tenant (or null)
- `POST /api/v1/tenant/select` — set org cookie after membership validation

## Login

Single-membership users receive org cookie automatically on login.

## Legacy fallback

When tenant cannot be resolved (no membership, DB unavailable, legacy env operator), bounded mutation guards return `None` and preserve pre-S2 env-operator paths for freeze compatibility.
