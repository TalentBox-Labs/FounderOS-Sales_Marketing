# M6 — Staging Smoke Test

**Agent:** Sentinel — Public Smoke Test  
**Sprint:** M6  
**Date:** 2026-08-10  
**Target:** Cloudflare Pages **staging URL**  

---

## Live URL testing

| Field | Value |
|-------|-------|
| Staging URL | **NOT CREATED** |
| Live HTTP smoke | **NOT RUN** (no remote deploy) |

Cloudflare Pages upload did not complete (missing `CLOUDFLARE_API_TOKEN`). Sentinel did **not** modify deployment artifacts.

---

## Package-level verification (pre-edge)

Executed against `output/website-deploy/packages/dep_m6_staging/`:

| Check | Result | Notes |
|-------|--------|-------|
| Expected content page | **PASS** | `hiring-systems/index.html` present |
| Home page `/` | **N/A** | No root `index.html` in Static v1.0 — expect **404** at `/` on Pages until landing page exists |
| CSS/JS/static assets | **N/A** | Not in package |
| Canonical URLs in HTML | **PASS** | Points to `https://workcrew.ai/blog/hiring-systems` (production URL in content; staging host will differ until canonical strategy for staging) |
| `sitemap.xml` | **PASS** | Present at package root |
| `rss.xml` | **PASS** | Present at package root |
| Private files exposed in package | **PASS** | No `metadata.json` / `source.md` |
| Directory listing | **N/A** | Cloudflare Pages default — verify after deploy |
| Invalid route | **N/A** | Verify after deploy (expect 404) |
| HTTPS | **N/A** | Requires live `*.pages.dev` URL |
| Repeated request stability | **N/A** | Requires live URL |

---

## Post-deploy smoke script (run when URL exists)

Replace `STAGING_BASE` with `https://<project>.pages.dev` or preview hash URL.

```bash
STAGING_BASE="https://NOT_CREATED"
curl -sS -o /dev/null -w "%{http_code}" "$STAGING_BASE/hiring-systems/"
curl -sS -o /dev/null -w "%{http_code}" "$STAGING_BASE/sitemap.xml"
curl -sS -o /dev/null -w "%{http_code}" "$STAGING_BASE/rss.xml"
curl -sS -o /dev/null -w "%{http_code}" "$STAGING_BASE/hiring-systems/metadata.json"   # expect 404
curl -sS -o /dev/null -w "%{http_code}" "$STAGING_BASE/hiring-systems/source.md"       # expect 404
curl -sS -o /dev/null -w "%{http_code}" "$STAGING_BASE/deployment-manifest.json"     # should 404 if stripped pre-upload
```

---

## Verdict

| Gate | Result |
|------|--------|
| Live staging smoke | **FAIL** (no URL) |
| Package pre-check | **PASS** |

**Overall staging smoke:** **FAIL** until Cloudflare staging URL is created and script above passes.
