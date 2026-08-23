# CRM / Residual Tenant Isolation Baseline v1.0

**Status:** FROZEN  
**Date:** 2026-08-17  
**Supersedes:** SaaS S3 implementation attestation  
**Builds on:** SaaS S2.5 Organization / Tenant Isolation Baseline v1.0 (unchanged)

## Scope frozen

| Perimeter | Status |
|-----------|--------|
| CRM API `/api/v1/crm/*` | FROZEN — 15 live routes tenant-guarded when TenantContext resolves |
| CRM mutation guards | FROZEN — 8/8 |
| CRM read isolation | FROZEN — 7/7 |
| Cockpit / Operator / MDG isolation | PRESERVED from S2.5 |
| QD / CO isolation | PRESERVED from S2/MC04/MC06 |
| Editorial/publishing reads | DEFERRED (global by design) |
| n8n webhooks | DEFERRED (integration-security sprint) |
| Connector credential vault | DOCUMENTED HIGH — not tenantized |

## Architecture (frozen)

```
IdentityContext → Organization Membership → TenantContext → scoped CRM access → frozen domain ops
```

## Critical risk #9 (S2.5)

**MITIGATED** when TenantContext resolves. Legacy API-key-only no-session path remains LOW / GLOBAL_BY_DESIGN.

## Database migrations

**0**

## Frozen domain contracts

**0 changes** — A1.5, A3.5, A4.5, MC04.5, MC06.5, UI2.5, OF1.5, MDG1.5, S1.5, S2.5
