# SaaS S2 — TenantContext Contract

## Definition

```
TenantContext = IdentityContext + Organization + Membership + Role
```

**Module:** `revenue_os/services/tenant_context.py`

## Server-derived authority

Client-supplied `organization_id`, `tenant_id`, `workspace_id`, or `role` **do not** grant authority. Hints may be supplied for navigation; membership is validated server-side.

## Public fields

Includes all `IdentityContext.as_public_dict()` fields plus:

- `organization_id`, `organization_name`, `organization_slug`
- `membership_id`, `membership_role`, `membership_status`

## Layering (required)

```
authenticated human
  AND tenant membership
  AND role authorization (VIEWER read-only)
  AND existing frozen HUMAN_ONLY domain rules
```

Role does **not** replace frozen domain authority.
