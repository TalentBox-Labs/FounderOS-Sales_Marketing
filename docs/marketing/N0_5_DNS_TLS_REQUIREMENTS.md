# N0.5 — Cipher DNS / TLS / Security Requirements

**Sprint:** N0.5  
**DNS / production changes:** **NONE** (Outcome B)  
**Secrets:** not recorded  

---

## Preconditions for safe custom-domain attach (when Founder ratifies)

| Requirement | Notes |
|-------------|-------|
| Explicit approved hostname | From FDR (apex and/or www / blog subdomain) |
| DNS ownership | Ability to create CNAME (subdomain) or Cloudflare zone / ALIAS (apex) |
| Cloudflare Pages project | Existing `founderos-staging` or dedicated production project |
| TLS | Cloudflare Pages automatic certificates after domain active |
| No token exposure | Use env var names only (`CLOUDFLARE_API_TOKEN`, …) |
| Rollback | Remove custom domain / revert DNS; Pages `*.pages.dev` remains |

---

## Recommended www/apex policy (proposal — not ratified)

Founder must choose one of:

1. Apex `example.com` + optional `www` redirect  
2. Subdomain only (e.g. `blog.example.com`) as site origin  
3. Path under existing brand host (requires host ownership + path routing)

**Cipher does not choose the brand.**

---

## Redirect policy (required after cutover)

| From | To | Expected |
|------|----|----------|
| `https://founderos-staging.pages.dev/*` | Approved origin (optional permanent) | Documented; avoid loops |
| `http://` approved host | `https://` | Automatic on Pages |
| Non-www ↔ www | Per FDR | Single hop |

**Status now:** **NOT IMPLEMENTED** (no approved domain; no cutover)

---

## Current security posture

| Item | Status |
|------|--------|
| HTTPS on `founderos-staging.pages.dev` | Previously verified PASS (M7.5) — **not re-cutover-tested** this sprint |
| Custom domain TLS | **NOT CONFIGURED** (CNAME pending / domain not ratified) |
| Credential exposure this sprint | **NONE** |

---

## Cipher verdict

Safe cutover requirements are documented. **No attach/DNS executed** pending Founder domain FDR.
