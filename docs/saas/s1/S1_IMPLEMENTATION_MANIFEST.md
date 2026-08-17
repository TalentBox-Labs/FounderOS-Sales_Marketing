# SaaS S1 — Implementation Manifest

**Sprint:** FOUNDER OS SaaS S1  
**Date:** 2026-08-14  
**Mode:** BOUNDED IMPLEMENTATION

## Implementation type

**MIXED**

- **COMPLETE_EXISTING** — `User` + bcrypt + `python-jose`
- **BUILD_NEW** — IdentityContext, cookie session, Jinja `/login` `/logout`, request context
- **CONNECT_EXISTING** — `_trusted_cockpit_operator()` now reads IdentityContext; frozen services unchanged

## Persistence decision (Phase 2)

| Item | Decision |
|------|----------|
| Model | REUSE `revenue_os.models.user.User` |
| Why persist | Restart-safe Owner; not session-only |
| Schema change | None |
| Alembic | None |
| Blast radius | Identity wrapper + three Founder HTML GETs + trusted actor |
| Rollback | Disable `FOUNDER_OS_REQUIRE_LOGIN`; env operator remains |
| Frozen impact | 0 contract files edited |
| Wrapper | Identity → `_trusted_cockpit_operator` → existing `requested_by` |

## Code

| Path | Change |
|------|--------|
| `revenue_os/services/identity_context.py` | NEW contract |
| `runner_api_routers/identity.py` | NEW auth routes + resolution |
| `templates/login.html` | NEW |
| `runner_api.py` | Middleware, router, bootstrap |
| `runner_api_routers/cockpit.py` | Trusted actor + operator status prefer session |
| `runner_api_routers/ui.py` | GET gate for cockpit/operator/register |
| `templates/base.html` | Optional sign-out |
| `.env.example` | Commented bootstrap keys |
| `tests/test_saas_s1_identity_foundation.py` | NEW |
| `docs/saas/s1/*` | NEW |

**Unchanged on purpose:** `qualified_demand.py`, `commercial_outcome.py`, `crm.py` request schemas; `mutation_authority.py`; User columns; operator_flow call sites (`_trusted_cockpit_operator()` × 8).

## Change control

| Item | Count |
|------|------:|
| Frozen contract changes | 0 |
| Tenant/domain migrations | 0 |
| Identity Alembic migrations | 0 |
| External integrations activated | 0 |
| Credentials committed | 0 |
| CRM SPA mounted | NO |
| Lovable | NO |
| Public signup | NO |

## Pass intent

Canonical Human Identity **IMPLEMENTED** on primary `runner_api`. Tenancy **NOT** started.

## Next

SaaS S1.5 — IDENTITY FOUNDATION BASELINE FREEZE  
Do not start S2 in this sprint.
