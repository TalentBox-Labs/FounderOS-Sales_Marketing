# SaaS S1 — S2 Tenancy Readiness

**Sprint:** FOUNDER OS SaaS S1  
**S2 status:** CONDITIONAL — identity exists; isolation does not

## Ready

- Canonical HUMAN vs SERVICE vs AGENT vs AI
- Persistent `User` without tenant columns (intentionally)
- IdentityContext designed so `TenantContext = IdentityContext + Organization`
- Founder mutation proxies already ignore client identity

## Not ready (S2 work)

- Organization model
- `organization_id` / `workspace_id` on tenant-owned entities
- Scoped queries for Contact / Company / Deal / logs / vault
- Membership (user ↔ org + role)
- Cross-tenant IDOR on ID-only mutations (S0 highest risk — still open)

## Do not do in S1.5/S2 accidentally

- Rewrite A3.5 / A4.5 / MC04.5 / MC06.5 semantics
- Treat API key as tenant owner
- Remount CRM SPA / Lovable as primary UI

## Recommended S2

**Organization model + TenantContext middleware + scoped query wrappers on ID-only mutations** — still IDENTITY-FIRST WRAP, still no Lovable.
