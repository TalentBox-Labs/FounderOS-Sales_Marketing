# SaaS S1 — IdentityContext Contract

**Sprint:** FOUNDER OS SaaS S1  
**Module:** `revenue_os/services/identity_context.py`

## Fields (no tenancy)

| Field | Type | Notes |
|-------|------|-------|
| `user_id` | UUID string \| null | Present for session humans |
| `email` | string \| null | From `User.email` |
| `display_name` | string \| null | From `User.full_name`; used as trusted `requested_by` |
| `role` | `owner` \| `admin` \| `member` \| `viewer` \| null | Persisted; **not** broadly enforced |
| `auth_method` | `session` \| `legacy_operator_env` \| `api_key` \| `none` | |
| `principal_kind` | `HUMAN` \| `SERVICE` \| `AGENT` \| `AI` \| `ANONYMOUS` | |
| `is_human` | bool | True only for verified HUMAN |
| `request_id` | optional | Reserved |

**Forbidden on this object in S1:** `tenant_id`, `organization_id`, `workspace_id`.

## Extensibility (S2)

```
TenantContext = IdentityContext + Organization context
```

Do not attach org IDs to Contact/Deal in S1.

## Binding rule

`bind_requested_by(ctx)` returns `display_name` only when `principal_kind is HUMAN` and `is_human_approver(display_name)`.

SERVICE / AGENT / AI / ANONYMOUS raise `PermissionError`.

## Runtime resolution

`identity_context_for_request(request)`:

1. Valid, non-revoked session cookie + active User → HUMAN (or non-human if name fails the human gate)
2. Matching `RUNNER_API_KEY` Bearer → SERVICE
3. Else ANONYMOUS

GET `/api/v1/identity/me` returns the public dict (no secrets, no password hash).
