# R0 — Engine Consolidation (HERMES)

**Date:** 2026-08-11 · **Mode:** AUDIT ONLY · **Frozen contracts:** UNCHANGED

---

## Canonical KEEP

| Engine | Path | Freeze |
|--------|------|--------|
| Content Studio | routers + templates + tracker/input | E3.5 / E4.5 |
| Editorial | `editorial_approval` + router | E6B.5 / E7 |
| Publishing | `publishing_engine` | M1.5 |
| Website Engine | `website_engine/` | M2.5 / M3.5 |
| Deployment Adapter | `website_deployment/` | M5.5 |
| SEO Readiness | `seo_engine/` | S1.5 |
| Technical SEO | `seo_engine/technical/` | S2.5 |

---

## Duplication / shadow

| Concern | Surfaces | Class |
|---------|----------|-------|
| Website publish wire | Publishing PLACEHOLDER vs live Website Engine | STALE GAP |
| Social publish | Publishing stubs + `/marketing/publish` + `social_publisher` | DEPRECATE adjacent |
| Go-live / Hashnode | `POST /go-live`, `hashnode_publish` | DEPRECATE legacy |
| Inventory UI | Content Studio + `/weeks` + pipeline | DEPRECATE weeks as primary later |
| SEO families | Readiness ⊥ Technical | KEEP BOTH (frozen) |
| Keyword CRUD on `/api/v1/seo` | Mixed with readiness | DEPRECATE mental model |
| Dual apps | `runner_api` vs `revenue_os.main` | DEPRECATE confusion |

---

## Cross-engine leakage (top)

1. Publishing does not invoke Website Engine.  
2. Website publish callable without Publishing audit.  
3. Marketing social path bypasses Publishing Engine.  
4. Go-live/Hashnode bypass Publishing.  
5. CMS branding on Marketing UI.

**Do not** merge Technical into Readiness; **do not** fold deploy into Publishing; **do not** treat Editorial approval as publish auth.
