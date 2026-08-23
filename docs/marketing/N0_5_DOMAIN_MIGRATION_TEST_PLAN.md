# N0.5 — Domain Migration Test Plan (Sentinel)

**Sprint:** N0.5  
**Execution:** **NOT RUN** (no approved domain / no DNS change)  

---

## Preconditions

1. Founder ratifies production domain (FDR-N05).  
2. DNS CNAME/ALIAS active; Cloudflare domain status active.  
3. Artifacts regenerated with ratified `SEO_PRODUCTION_ORIGIN`.  
4. Optional: redirects from `founderos-staging.pages.dev`.

---

## Test matrix (run after cutover)

| # | Check | Method | Pass criteria |
|---|-------|--------|---------------|
| 1 | HTTPS on approved origin | `curl -I https://<origin>/…` | TLS OK, HTTP 2xx/3xx as designed |
| 2 | Page content | GET `/<slug>/` | 200; expected title |
| 3 | Redirect old host | GET `https://founderos-staging.pages.dev/<slug>/` | If policy enabled: single 301/302 to origin; **no loop** |
| 4 | Canonical | HTML head | `rel=canonical` host == approved origin |
| 5 | Sitemap | GET `/sitemap.xml` | Every `<loc>` uses approved origin |
| 6 | RSS | GET `/rss.xml` | Channel/item links use approved origin |
| 7 | Assets | N/A for RC1 | Still N/A until assets exist |
| 8 | 404 | Unknown path | Explicit 404; no loop |
| 9 | Stability | Repeat GET ×2 | Same status |
| 10 | Private files | `metadata.json` / `source.md` | 404 |
| 11 | Host/canonical alignment | Compare | **PASS** |

---

## Current claim

| Gate | Status |
|------|--------|
| Migration tests | **NOT TESTED** (blocked) |
| Host/Canonical Alignment | **FAIL** (known mismatch; unchanged) |

Do not claim PASS until this plan is executed against a ratified host.
