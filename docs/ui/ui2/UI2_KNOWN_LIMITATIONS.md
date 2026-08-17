# UI2 — Known Limitations

**Sprint:** UI2 v1  
**Date:** 2026-08-13

1. **Operator configuration required** — Human actions need `FOUNDER_OS_OPERATOR_NAME` set to a valid human name.
2. **No UI session auth** — Cockpit HTML routes follow existing open-dev Jinja pattern; API routes use `_verify_api_key`.
3. **Sales DB dependency** — Attention queue and sales snapshot require PostgreSQL; show unavailable when down.
4. **QualifiedDemand reject deferred** — Accept only in v1.
5. **Deal stage / editorial / publishing mutations deferred** — Link-outs to existing pages only.
6. **Revenue outcome** — Commercial flow shows EMERGING / NOT YET ACTIVE honestly.
7. **Social live** — Blocked; not implied as active.
8. **Production SEO** — Blocked; panels label activation BLOCKED.
9. **CRM React SPA** — Remains unmounted.
10. **Branding** — Shell visible text updated to Founder OS; API health strings still reference WorkCrew CMS OS (internal identifiers unchanged).
