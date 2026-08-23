# CANONICAL USER CONTRACT v1.0

**STATUS: FROZEN**  
**Sprint:** FOUNDER OS SaaS S1.5  
**Model path:** `revenue_os.models.user.User`  
**Table:** `users`

## Frozen identity semantics

| Concern | Contract |
|---------|----------|
| Canonical identifier | `User.id` (UUID) |
| Login identifier | `User.email` (unique, case-normalized to lowercase at auth) |
| Password credential | `User.hashed_password` — bcrypt via `revenue_os.auth.hash_password` / `verify_password` |
| Display / trusted actor name | `User.full_name` — must pass `is_human_approver` for HUMAN login and HUMAN_ONLY binding |
| Role representation | `User.role` string; MVP vocabulary `owner` \| `admin` \| `member` \| `viewer` |
| Active / disabled | `User.is_active` — truthy required for session acceptance and login |

## Fields NOT part of frozen S1 identity contract

| Field | Disposition |
|-------|-------------|
| `avatar_url` | Unrelated baggage — not identity authority |
| `preferences` | Unrelated baggage — not identity authority |
| `created_at` / `updated_at` | Audit timestamps only |

## Architectural note

The `User` model originates under `revenue_os` and may carry future domain baggage. S1.5 freezes **identity semantics only**. Relocation or slim identity table is a future concern — **not** an S1.5 change.

## Forbidden on User in this baseline

- `tenant_id`
- `organization_id`
- `workspace_id`

## Bootstrap interaction

Initial OWNER may be created by `bootstrap_owner_if_needed()` when env credentials are present and email is absent. See `OWNER_BOOTSTRAP_CONTRACT_v1.0.md`.
