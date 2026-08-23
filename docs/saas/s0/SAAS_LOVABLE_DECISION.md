# SaaS S0 — Lovable Decision

**Sprint:** SaaS S0  
**Date:** 2026-08-13  
**Mode:** AUDIT ONLY — Lovable NOT used

| Role | Classification |
|------|----------------|
| Visual prototyping | **USE** |
| Design system exploration | **USE** |
| Authenticated SaaS shell prototype | **CONDITIONAL** |
| Dashboard UX prototype | **CONDITIONAL** |
| Production frontend | **DO_NOT_USE** |
| Backend generation | **DO_NOT_USE** |
| Database ownership | **DO_NOT_USE** |
| Authentication ownership | **DO_NOT_USE** |

## Constraint

```
Lovable UI → Founder OS existing APIs → Frozen contracts → Canonical SoTs
```

Forbidden: Lovable DB / duplicate domain / client-trusted authority.

## Recommended Lovable Timing

**AFTER SaaS S1 Identity Foundation** for authenticated shell prototypes.  
**AFTER_SAAS_ARCHITECTURE** (tenant wrappers live) for any serious FE exploration.  
**NEVER** for production backend/auth/DB.
