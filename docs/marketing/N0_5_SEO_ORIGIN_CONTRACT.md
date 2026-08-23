# N0.5 — SEO Origin Contract (Hermes)

**Sprint:** N0.5  
**Status:** CONTRACT DRAFT — origin **pending Founder ratification**  
**Code changes:** 0  

---

## Authoritative production origin (to be filled after FDR)

```text
SEO_PRODUCTION_ORIGIN = https://<APPROVED_PRODUCTION_DOMAIN>
```

Until FDR Accept:

| Field | Value |
|-------|-------|
| Authoritative origin | **NOT RATIFIED** |
| Temporary public host (certified) | `https://founderos-staging.pages.dev` |
| Embedded content default | `https://workcrew.ai/blog` (**not** ratified as SEO origin) |

---

## Surfaces that MUST derive from SEO_PRODUCTION_ORIGIN

| Surface | Rule |
|---------|------|
| Canonical `<link rel="canonical">` | Absolute URL under origin |
| OpenGraph `og:url` | Same as canonical (or explicit policy) |
| Schema.org `@id` / `url` | Same origin |
| Sitemap `<loc>` | Absolute URLs under origin |
| RSS channel `link` + item `link` | Absolute URLs under origin |
| Internal absolute links (if any) | Same origin |
| robots / sitemap declaration | Host that serves the site |
| Search Console / analytics property | Same origin host |
| Cloudflare custom domain | Must match origin host (apex or subdomain policy in FDR) |

---

## Forbidden after ratification

- Independent hardcoded hostnames in Website Engine defaults that disagree with FDR origin  
- Publishing Engine inventing hosts  
- SEO Engine scoring against a host that is not the ratified origin  
- Treating `*.pages.dev` as long-term SEO origin once custom domain is ratified (unless FDR explicitly chooses pages.dev)

---

## Implementation note (future — not N0.5)

Website Engine already accepts `site_base` / front-matter `canonical_url`. After FDR, set a single configured origin; regenerate artifacts; align DNS. **Do not** start SEO Engine until origin is ratified.

---

## Hermes status

**SEO Origin Contract: DEFINED as policy · ORIGIN VALUE: BLOCKED ON FOUNDER DECISION**
