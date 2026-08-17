# FDR-N05 — Production Website Domain (Founder Decision Record)

**Sprint:** N0.5 — Production Domain & SEO Identity Gate  
**Date:** 2026-08-10  
**Status:** **OPEN — AWAITING FOUNDER ACCEPT**  
**Blocks:** SEO Engine implementation · branded DNS cutover · SEO origin freeze  
**Code / DNS / architecture changes until Accept:** **FORBIDDEN**

---

## Problem

Founder OS Website v1.0 is certified live on:

`https://founderos-staging.pages.dev`

Content and Website Engine defaults embed:

`https://workcrew.ai/blog/...`

N0 found **no founder-ratified** production domain. Using either host as “the” SEO origin without Accept would create incorrect Search Console / canonical / branding truth.

---

## Evidence (not ratification)

| Item | Meaning |
|------|---------|
| `DEFAULT_SITE_BASE = https://workcrew.ai/blog` | Engineering default |
| Content `canonical_url` fields | Bundle convention |
| M7 Cloudflare attach of `workcrew.ai` | Ops attempt; DNS pending; **not** FDR |
| M7.5 baseline | Certifies pages.dev host |

---

## Decision required

**FDR-N05:** What is the authoritative production website origin for Founder OS Website + future SEO Engine?

### Options (choose exactly one)

| Option | Origin example shape | Implications |
|--------|----------------------|--------------|
| **A** | Keep temporary `https://founderos-staging.pages.dev` as SEO origin | Update defaults/canonicals/feeds to pages.dev; unusual branding; SEO on pages.dev |
| **B** | `https://workcrew.ai` (apex) with path policy (e.g. `/blog`) | Requires DNS ownership + apex strategy; regenerate artifacts |
| **C** | `https://blog.workcrew.ai` (or similar subdomain) as origin | CNAME to Pages; regenerate artifacts; path policy |
| **D** | Other Founder-owned hostname: `https://________________` | Founder supplies exact host; prove DNS control |
| **E** | Defer SEO Engine; leave mismatch until later | SEO remains **BLOCKED**; site stays on pages.dev |

### Also specify (if B/C/D)

1. Apex vs www policy (redirect direction)  
2. Whether `founderos-staging.pages.dev` should 301 to the approved origin  
3. Whether existing `workcrew.ai` content elsewhere must not be broken  

---

## Selected Option

| Field | Value |
|-------|-------|
| Selected Option | _blank_ |
| Exact origin URL | _blank_ |
| www/apex policy | _blank_ |
| Redirect old pages.dev? | YES / NO / _blank_ |
| Approved | **NO** |
| Founder sign-off | _blank_ |
| Date | _blank_ |

---

## After Accept (future sprint — not N0.5)

1. Configure Cloudflare custom domain + DNS  
2. Set Website Engine origin / regenerate public package  
3. Run [N0_5_DOMAIN_MIGRATION_TEST_PLAN.md](../marketing/N0_5_DOMAIN_MIGRATION_TEST_PLAN.md)  
4. Freeze **new** production identity baseline (do not rewrite M7.5)  
5. Unblock SEO Engine authorization  

---

## Related

- [N0_5_DOMAIN_IDENTITY_AUDIT.md](../marketing/N0_5_DOMAIN_IDENTITY_AUDIT.md)  
- [N0_5_SEO_ORIGIN_CONTRACT.md](../marketing/N0_5_SEO_ORIGIN_CONTRACT.md)  
- [N0_PRODUCTION_DOMAIN_IDENTITY.md](../operations/N0_PRODUCTION_DOMAIN_IDENTITY.md)  
- [FOUNDER_OS_WEBSITE_V1_PRODUCTION_BASELINE.md](../operations/FOUNDER_OS_WEBSITE_V1_PRODUCTION_BASELINE.md)
