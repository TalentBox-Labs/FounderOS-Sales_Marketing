# Product Tenancy Audit

**Sprint:** MDG0  
**Date:** 2026-08-13  
**Mode:** AUDIT ONLY

## Classification

**SINGLE_USER** (product reality)

With orphaned multi-user scaffolding on the secondary JWT app (`User` model + register/login) that is **not** the primary `runner_api` shell.

## Evidence

| Concept | Finding |
|---------|---------|
| User | `revenue_os/models/user.py` — email, password hash, `role` string; used by secondary JWT app |
| Account / Workspace / Organization / Tenant / Membership | **Absent** as app tenancy models |
| `tenant_id` / `organization_id` / `workspace_id` on CRM/content SoTs | **Absent** |
| Team | `TeamMember` is CRM staffing on contacts — not app tenancy |
| RBAC enforcement | `User.role` stored; no systematic `require_role` on primary routers |
| Secrets | Credential vault keyed by `connector_name` — instance-global |
| Query scoping | Contact / Deal / Company / AgentActionLog are global tables |

## Answers

| Question | Answer |
|----------|--------|
| Authenticated users on primary shell? | Shared `RUNNER_API_KEY` for APIs; Jinja pages largely unauthenticated |
| Multiple users? | Possible only on secondary JWT app; not productized for Founder OS shell |
| Multiple organizations? | NO |
| Data partitioned by tenant? | NO |
| Tenant-aware authorization? | NO |
| Config / secrets | Per deployment, not per tenant |
| Onboarding tenant-aware? | NO |

## Not

- MULTI_TENANT_PARTIAL
- MULTI_TENANT_READY
