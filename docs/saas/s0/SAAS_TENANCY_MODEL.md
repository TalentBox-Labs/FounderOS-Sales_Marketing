# SaaS S0 — Tenancy Model

**Sprint:** SaaS S0  
**Date:** 2026-08-13  
**Mode:** AUDIT ONLY

## Existing Tenant Model: NO

| Candidate | Semantics | Suitable as SaaS tenant? |
|-----------|-----------|--------------------------|
| `Company` | CRM customer firm | **NO** — domain object |
| `Client` | Billing client linked to Company | **NO** |
| `TeamMember` | Project staffing | **NO** |
| `User` | Global email-unique account | **NO** — lacks org membership |
| Outlook `tenant_id` | Azure AD connector field | **NO** — external IdP |

No `Organization`, `Workspace`, or SaaS `tenant_id` columns on CRM/audit models.

## Recommended canonical isolation model

**ORGANIZATION**

Optional **WORKSPACE** later if multi-brand/environments per customer.

### Why ORGANIZATION first

1. Maps to “customer of Founder OS” (billing + isolation root).
2. Current product is one founder world — no evidence of multi-workspace needs yet.
3. Do **not** overload CRM `Company` as tenant.
4. Prefer:

```
Organization Context
    ↓
Frozen Domain Contracts (MC04.5 / MC06.5 / A3.5 / A4.5 / …)
```

over rewriting frozen domain semantics.

## Current Tenancy classification

**SINGLE_USER** (product reality) with orphaned multi-user JWT scaffolding.
