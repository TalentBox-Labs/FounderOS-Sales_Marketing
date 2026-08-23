# SaaS S0 — Migration Strategies

**Sprint:** SaaS S0  
**Date:** 2026-08-13  
**Mode:** AUDIT ONLY

Scores 0–5 (higher = better). Migration Risk inverted as “safety” (5 = low risk).

## Strategy A — Identity-first wrap of current FastAPI/Jinja (RECOMMENDED)

Add real identity/session on `runner_api`; keep Jinja; later add Organization + query wrappers around frozen services.

| Criterion | Score |
|-----------|------:|
| Architecture Safety | 5 |
| Migration Risk (low=5) | 5 |
| Engineering Cost (low=5) | 4 |
| Time to SaaS | 3 |
| UX Potential | 3 |
| Frozen Contract Preservation | 5 |
| Future Scalability | 4 |
| **Total** | **29** |

## Strategy B — Authentication + tenancy schema first, FE later

Introduce Organization + `organization_id` columns + middleware before UX polish.

| Criterion | Score |
|-----------|------:|
| Architecture Safety | 4 |
| Migration Risk | 3 |
| Engineering Cost | 2 |
| Time to SaaS | 2 |
| UX Potential | 3 |
| Frozen Contract Preservation | 4 |
| Future Scalability | 5 |
| **Total** | **23** |

Higher blast radius (migrations) before identity UX exists — risk of incomplete auth binding.

## Strategy C — New SaaS frontend over frozen APIs (SPA/Lovable)

Build modern FE against existing APIs while backend remains instance-global.

| Criterion | Score |
|-----------|------:|
| Architecture Safety | 2 |
| Migration Risk | 1 |
| Engineering Cost | 1 |
| Time to SaaS | 2 |
| UX Potential | 5 |
| Frozen Contract Preservation | 2 |
| Future Scalability | 3 |
| **Total** | **16** |

Looks like SaaS; does not isolate data. Highest authority-divergence risk.

## Recommended

**Strategy A**

## Blast radius (tenancy later)

| Class | Items |
|-------|-------|
| MUST_CHANGE | Identity on runner_api; org membership; scoped queries; vault keying; FS isolation if multi-tenant hosted |
| MAY_CHANGE | Jinja branding; Celery context; Render topology; Alembic discipline; rate limits |
| MUST_NOT_CHANGE | Frozen domain semantics (A3.5/A4.5/MC04.5/MC06.5/UI2.5/OF1.5/MDG1.5); ownership boundaries; client-trusted identity |
