# ROLE VOCABULARY v1.0

**STATUS: FROZEN (vocabulary only)**  
**Sprint:** FOUNDER OS SaaS S1.5

## Frozen vocabulary

| Role | Meaning (informational) |
|------|-------------------------|
| OWNER | Bootstrap / instance owner; future tenant owner |
| ADMIN | Privileged operator |
| MEMBER | Default `User.role` |
| VIEWER | Read-intended |

Normalization: `revenue_os.services.identity_context.normalize_role` / `MVP_ROLES`.

## Enforcement

**DEFERRED_TO_S2**

S1.5 intentionally does **not** freeze broad endpoint authorization. HUMAN_ONLY via `is_human_approver` remains the mutation gate.

## Explicit non-claims

- VIEWER is not yet denied mutations by role
- ADMIN is not yet endpoint-enforced
- No tenant membership roles
