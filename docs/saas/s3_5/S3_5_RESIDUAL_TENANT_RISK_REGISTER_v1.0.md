# S3.5 — Residual Tenant Risk Register v1.0

| # | Risk | Severity | Classification | Post-S3 status |
|---|------|----------|----------------|----------------|
| 1 | CRM API ungated ID-only | CRITICAL | S3_REQUIRED | **MITIGATED** (TenantContext active) |
| 2 | Global connector credential vault | HIGH | FUTURE_SECURITY / S4 | DOCUMENTED |
| 3 | Editorial/publishing read surfaces | MEDIUM | DEFERRED_PRODUCT | DEFERRED |
| 4 | n8n/webhook handlers unscoped | MEDIUM | S4_REQUIRED | DEFERRED |
| 5 | Legacy API-key-only no-session CRM | LOW | GLOBAL_BY_DESIGN | PRESERVED |
| 6 | Multi-org switcher UX absent | LOW | DEFERRED_PRODUCT | API exists; UX later |

## Summary

**Critical residual tenant risks:** NONE (when TenantContext resolves)

**High residual tenant risks:**
- Global connector credential vault (no `organization_id`)

**Medium residual tenant risks:**
- Editorial/publishing reads (global content tracker)
- n8n webhooks (`_load_contact` by payload ID without tenant)

**Low residual tenant risks:**
- Legacy no-tenant CRM fallback
- Multi-org UX switcher

## New critical risks found in S3.5 audit

**NONE** — freeze not blocked.
