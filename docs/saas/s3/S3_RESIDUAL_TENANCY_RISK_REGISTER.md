# S3 — Residual Tenancy Risk Register

| # | Risk | Severity | Classification | S3 status |
|---|------|----------|----------------|-----------|
| 1 | CRM API ungated | CRITICAL | S3_REQUIRED | **MITIGATED** |
| 2 | Global connector vault | HIGH | FUTURE_SECURITY | DOCUMENTED |
| 3 | Editorial/publishing reads | MEDIUM | S3_REQUIRED | **DEFERRED** (global by design) |
| 4 | n8n webhooks | MEDIUM | Integration sprint | **DEFERRED** |
| 5 | Legacy no-tenant CRM fallback | LOW | GLOBAL_BY_DESIGN | PRESERVED |
| 6 | Multi-org switcher UX | LOW | S3_REQUIRED | API `/tenant/select` exists; UX deferred |

**Critical residual tenant risks:** NONE (when tenant context active)

**High residual:** Global connector vault (unchanged)
