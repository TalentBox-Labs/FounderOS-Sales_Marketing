# SaaS S2 — Residual Tenancy Gaps

## Out of S2 scope (documented)

1. Ungated CRM API (`/api/v1/crm/*`) — ID-only mutations possible
2. Global connector credentials — no tenant vault
3. Editorial / publishing / SEO read surfaces — not org-filtered
4. Pipeline / Company — not tenant-scoped
5. Multi-org user UX (org switcher UI) — API only (`/api/v1/tenant/select`)
6. Broad repository query tenant wrapping

## Recommended S3

Bounded read isolation expansion + CRM API tenant guards + org switcher UX.
