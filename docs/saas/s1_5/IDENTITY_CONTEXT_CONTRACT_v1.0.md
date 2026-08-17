# IDENTITY CONTEXT CONTRACT v1.0

**STATUS: FROZEN**  
**Sprint:** FOUNDER OS SaaS S1.5  
**Module:** `revenue_os/services/identity_context.py`

## Abstraction

```
Authenticated Request
        ↓
IdentityContext
        ↓
Authority Adapter
        ↓
Frozen Domain Operation
```

## Frozen fields

| Field | Allowed values / notes |
|-------|------------------------|
| `principal_kind` | `HUMAN` \| `SERVICE` \| `AGENT` \| `AI` \| `ANONYMOUS` |
| `auth_method` | `session` \| `legacy_operator_env` \| `api_key` \| `none` |
| `is_human` | `true` only for verified HUMAN |
| `user_id` | UUID string or null |
| `email` | string or null |
| `display_name` | trusted actor label source for humans |
| `role` | normalized MVP role or null |
| `request_id` | optional / reserved |

## Forbidden fields (S1.5)

`tenant_id`, `organization_id`, `workspace_id`

## Classification rules (frozen)

| Kind | Meaning |
|------|---------|
| HUMAN | Verified human session (or legacy env operator path for actor binding) |
| SERVICE | `RUNNER_API_KEY` / system — never HUMAN |
| AGENT | Agent/automation labels — never HUMAN_ONLY authority |
| AI | AI/LLM labels — never HUMAN_ONLY authority |
| ANONYMOUS | No trusted credentials |

## Binding

`bind_requested_by(ctx)` returns `display_name` **only** for HUMAN with `is_human` and `is_human_approver`. SERVICE / AGENT / AI / ANONYMOUS raise `PermissionError`.

## Future extension

```
TenantContext = IdentityContext + Organization context
```

S2 must wrap/extend — not replace — this contract.
