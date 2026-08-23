# SaaS S0 — RBAC Matrix

**Sprint:** SaaS S0  
**Date:** 2026-08-13  
**Mode:** AUDIT ONLY

## MVP RBAC Recommendation

**OWNER · ADMIN · MEMBER · VIEWER**

Derived from existing human-gated mutations; not enterprise ABAC.

Today: API key possession ≈ OWNER of entire instance; `User.role` is unused.

## Matrix (proposed)

| Action | VIEWER | MEMBER | ADMIN | OWNER |
|--------|:------:|:------:|:-----:|:-----:|
| Read cockpit / operator snapshot | ✓ | ✓ | ✓ | ✓ |
| MDG1 manual demand register | | ✓ | ✓ | ✓ |
| QD accept / reject | | | ✓ | ✓ |
| Contact.status update | | ✓ | ✓ | ✓ |
| Deal create / stage update | | ✓ | ✓ | ✓ |
| CommercialOutcome handoff | | ✓ | ✓ | ✓ |
| Revenue CO accept / reject | | | ✓ | ✓ |
| Editorial approve | | ✓ | ✓ | ✓ |
| Publishing promote / go-live | | | ✓ | ✓ |
| Connector vault R/W | | | ✓ | ✓ |
| Invite users / change roles | | | | ✓ |
| Org billing / delete org | | | | ✓ |

## Mapping from current gates

| Current gate | SaaS evolution |
|--------------|----------------|
| `is_human_approver(name)` | Bind to authenticated User + role |
| `FOUNDER_OS_OPERATOR_NAME` | Become session user display name / membership |
| Client `requested_by` | **Eliminate** as authority; keep as audit display only if bound |
| Shared API key | Service/machine credentials only; not human UX |

Do not over-engineer beyond this MVP until tenancy ships.
