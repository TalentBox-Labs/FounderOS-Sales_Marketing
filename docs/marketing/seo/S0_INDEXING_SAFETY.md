# S0 — Indexing Safety Controls

**Sprint:** S0  
**Agent:** CIPHER  
**Implementation:** `src/tools/site_origin.py`

---

## 1. Objective

Prevent accidental search-engine indexing against:

- Staging hostnames (`*.pages.dev`, `founderos-staging.pages.dev`)
- Test / preview deployments
- Unratified or placeholder origins
- Deprecated production hosts (`workcrew.ai`)

**No automatic search-engine submission. No autonomous indexing authorization.**

---

## 2. Activation gate

Production SEO activation requires **all** of:

```text
FOUNDER_SITE_ORIGIN          → set to ratified production origin (not placeholder)
FOUNDER_SITE_ORIGIN_RATIFIED → 1 | true | yes
Origin host                  → not in DEPRECATED_PRODUCTION_HOSTS
Origin host                  → not in INFRASTRUCTURE_HOSTS / *.pages.dev
```

API: `is_indexing_activation_allowed() -> bool`

Default (S0): **False**

---

## 3. Host classifications

| Host pattern | Treatment |
|--------------|-----------|
| `example.invalid` | Placeholder — indexing blocked |
| `workcrew.ai`, `blog.workcrew.ai` | Deprecated — indexing blocked even if ratified flag set |
| `founderos-staging.pages.dev`, `*.pages.dev` | Infrastructure — indexing blocked |
| Ratified future domain | Allowed **only** with explicit `FOUNDER_SITE_ORIGIN_RATIFIED` |

Helpers: `is_deprecated_production_host()`, `is_infrastructure_host()`

---

## 4. Controls not in S0 (S1+ backlog)

| Control | Status |
|---------|--------|
| `<meta name="robots" content="noindex,nofollow">` on staging builds | NOT IMPLEMENTED |
| Cloudflare `_headers` / Workers `X-Robots-Tag` | NOT IMPLEMENTED |
| `robots.txt` disallow for infra hosts | NOT IMPLEMENTED |
| Search Console verification | BLOCKED |
| Sitemap ping / IndexNow | BLOCKED |
| DNS changes | BLOCKED |

---

## 5. Deployment adapter safety

Website Deployment Adapter (`src/tools/website_deployment/`) exports static artifacts only. It does **not**:

- Register sitemaps with search engines
- Set indexing headers
- Attach custom domains

Deploy to `founderos-staging.pages.dev` must be treated as **non-indexable infrastructure** until domain + SEO activation gates pass.

---

## 6. Operational rules

1. Do not set `FOUNDER_SITE_ORIGIN_RATIFIED` until Founder ratifies domain (FDR-N05).
2. Do not submit `sitemap.xml` to Google/Bing in S0/S1 without explicit founder authorization.
3. Preview deployments inherit infrastructure classification.
4. Readiness WARNING on `deprecated_host` or `infrastructure_host` is expected pre-ratification.

---

## 7. Verdict

**Production SEO Activation:** BLOCKED (by design)  
**Safety contract:** READY — gates defined in code; edge headers deferred to S1
