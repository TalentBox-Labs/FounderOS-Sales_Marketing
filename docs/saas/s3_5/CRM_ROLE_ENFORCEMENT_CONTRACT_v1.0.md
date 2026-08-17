# CRM Role Enforcement Contract v1.0

**Vocabulary (frozen from S2.5):** OWNER, ADMIN, MEMBER, VIEWER

## Rules

1. Role is resolved from `OrganizationMembership` via `TenantContext`.
2. Role in Org A does **not** confer authority in Org B.
3. Role enforcement is **additive** to authenticated human identity + tenant membership + HUMAN_ONLY domain rules.
4. Service/Agent/AI identities cannot use membership role to bypass HUMAN_ONLY gates.

## CRM behavior (frozen)

| Role | Read (when tenant resolves) | Mutation |
|------|----------------------------|----------|
| OWNER | Allowed | Allowed (subject to HUMAN_ONLY on A3/A4) |
| ADMIN | Allowed | Allowed (subject to HUMAN_ONLY) |
| MEMBER | Allowed | Allowed (subject to HUMAN_ONLY) |
| VIEWER | Allowed | **BLOCKED** (403 via `optional_tenant_mutation`) |

## HUMAN_ONLY preserved

- `PATCH /contacts/{id}/status` — `is_human_approver(requested_by)` required
- `PATCH /deals/{id}/stage` — `is_human_approver(requested_by)` required

Role alone never grants Agent/AI/Service mutation authority on these routes.
