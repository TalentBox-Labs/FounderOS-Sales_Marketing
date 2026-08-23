# Product Auth Readiness

**Sprint:** MDG0  
**Date:** 2026-08-13  
**Mode:** AUDIT ONLY

## Current model (primary app = `runner_api`)

| Mechanism | State |
|-----------|-------|
| Login UI (Jinja) | **Absent** |
| Shared API key | `RUNNER_API_KEY` Bearer (`runner_api_routers/utils.py`) |
| Auth-off risk | If key unset, API open |
| Trusted human mutations | `FOUNDER_OS_OPERATOR_NAME` server-side; client `requested_by` not trusted |
| Agent / AI mutation | Blocked (`is_human_approver`, `HumanAuthorityError`) |
| React CRM login | Team API key in localStorage — not password SSO |
| JWT / password / register | On **secondary** `revenue_os.main` only — not mounted in runner shell |
| OAuth (app SSO) | Absent (connector OAuth for Gmail etc. only) |
| Roles / invite / password reset | Not productized on primary path |
| Logout | SPA localStorage clear only |

## Sufficiency

| Target | Ready? |
|--------|--------|
| A. Founder-only hosted product | **MOSTLY YES** — with network controls + API key + operator env |
| B. Company / team use | **WEAK** — shared key; Jinja HTML unauthenticated; weak per-user audit identity |
| C. Multi-tenant SaaS | **NO** |

## Summary

Current authentication readiness: **founder-operated shared-secret + trusted-operator env; not SaaS identity.**

Do not build a new auth system in MDG0/MDG1 unless scoped as a dedicated auth sprint.
