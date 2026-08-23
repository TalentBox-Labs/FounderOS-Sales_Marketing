# M4 — Cloudflare Pages Evaluation

**Status:** ANALYSIS ONLY — **NO deploy · NO Cloudflare resources · NO code**  
**Sprint:** M4 (provider candidate addendum)  
**Date:** 2026-08-10  
**Canonical repository:** `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`  
**Architecture:** v2.2 / ADR-003  
**Package SoT:** [M4_WEBSITE_DEPLOYMENT_PACKAGE.md](M4_WEBSITE_DEPLOYMENT_PACKAGE.md)  
**Boundary SoT:** [M4_ARCHITECTURE_DECISION.md](M4_ARCHITECTURE_DECISION.md)

---

## Verdict

| Field | Value |
|-------|-------|
| **Candidate** | Cloudflare Pages |
| **Fit to Founder Website Engine static output** | **YES** (after public-subset packaging) |
| **Free-plan suitable for first production** | **YES** (Founder brochure/blog scale) |
| **Provider Independent architecture preserved** | **YES** — host remains behind Deployment Adapter |
| **Inside Website Engine Core?** | **NO** — forbidden |
| **Recommendation** | **CLOUDFLARE PAGES** as first production static deployment **provider** |

---

## 1. Boundary (non-negotiable)

```text
Website Engine Core / Static Provider
        ↓  (local artifacts: output/website/)
Deployment Adapter  (M5+)
        ↓  (public-subset package + host transport)
Cloudflare Pages    (Hosting Platform — dumb edge)
```

| Rule | Status |
|------|--------|
| Core must never import Cloudflare SDK / Wrangler / Pages APIs | **REQUIRED** |
| Cloudflare credentials live in Shared Platform / Automation secrets | **REQUIRED** |
| Publishing Engine never owns Pages deploy | **REQUIRED** |
| M4 creates no Pages project, DNS, or API tokens | **VERIFIED** (analysis only) |

---

## 2. Static output compatibility

Founder artifact (Nova / Static Provider v1.0):

```text
output/website/
├── {slug}/index.html      ← public
├── {slug}/metadata.json   ← operator; NOT public by default
├── {slug}/source.md       ← operator; NOT public by default
├── sitemap.xml            ← public
└── rss.xml                ← public
```

| Requirement | Cloudflare Pages | Compatibility |
|-------------|------------------|---------------|
| Serve directory URLs `/{slug}/` via `{slug}/index.html` | Standard static hosting behavior | **PASS** |
| Serve `sitemap.xml` / `rss.xml` at site root | Static file serve | **PASS** |
| No CSS/JS/image assets required today | Pure HTML/XML tree | **PASS** |
| Exclude operator files from public edge | Adapter must package public subset (or `_headers` deny); **not** Core | **PASS** (adapter duty) |
| Root `/` landing page | Not generated today | **NOT BLOCKING** — same gap on any host |
| Max file size / file count | Free: 25 MiB/file, 20,000 files/site | **PASS** at current volume |
| Build step | Optional — Direct Upload or git of **pre-built** public tree; Founder does not need Pages to compile Python/Core | **PASS** |

**Conclusion:** Compatible with FounderOS static output when the Deployment Adapter ships the **public subset**, not the raw operator tree.

---

## 3. Requirements checklist

### 3.1 Free-plan suitability

Evidence: [Cloudflare Pages limits](https://developers.cloudflare.com/pages/platform/limits/), [Pages product page](https://pages.cloudflare.com/).

| Free-plan capability | Value | Founder fit |
|----------------------|-------|-------------|
| Static requests / bandwidth | Unlimited (per product free tier messaging) | **YES** |
| Builds / month | 500 (account-wide concurrent: 1) | **YES** for infrequent Founder publishes |
| Custom domains / project | 100 | **YES** |
| Files / site | 20,000 | **YES** |
| Max file size | 25 MiB | **YES** |
| Projects / account | 100 | **YES** |
| Paid required for static brochure/blog? | **No** | Meets M4 “prefer free” constraint |

**Watch-outs (non-blocking):** free-tier policy can change; 500 builds/month is account-wide; apex domains prefer Cloudflare DNS zone.

### 3.2 Custom domain support

Evidence: [Custom domains](https://developers.cloudflare.com/pages/configuration/custom-domains/).

| Item | Status |
|------|--------|
| Custom domains on Free | **YES** (up to 100 / project) |
| Subdomain via CNAME → `*.pages.dev` | **YES** (zone need not be on Cloudflare) |
| Apex domain | **YES** if domain is a Cloudflare zone with Cloudflare nameservers |
| Align with `canonical_url` | **Operator duty** — DNS/host must match URLs already embedded in HTML/feeds |

### 3.3 HTTPS

| Item | Status |
|------|--------|
| TLS on `*.pages.dev` | Automatic |
| TLS on custom domains | Automatic certificate provisioning |
| Founder cert ops | **None** for standard path |
| CAA conflicts | Documented; operator may need CAA allow for Cloudflare CAs |

### 3.4 Git-backed deployment

| Item | Status |
|------|--------|
| GitHub / GitLab connect | Native Pages flow |
| Production branch → production deploy | Supported |
| Fit to FounderOS | Prefer **deploy repo or artifact branch** containing **public subset only** — do not force Website Engine Core into Cloudflare build tooling |
| Alternative transport | **Direct Upload** (Wrangler / API) — better for “adapter pushes files” without committing HTML into the app monorepo |

Both git-backed and direct-upload stay **outside Core**.

### 3.5 Preview deployments

Evidence: [Preview deployments](https://developers.cloudflare.com/pages/configuration/preview-deployments/).

| Item | Status |
|------|--------|
| Unique preview URL per PR/commit | **YES** |
| Unlimited active previews | **YES** (documented) |
| Production / custom domains unaffected | **YES** |
| Access control for previews | Optional Cloudflare Access |

Useful for M5+ staging of generated public trees without exposing production.

### 3.6 Rollback / deployment history

Evidence: [Rollbacks](https://developers.cloudflare.com/pages/configuration/rollbacks/).

| Item | Status |
|------|--------|
| Deployment history in dashboard | **YES** |
| Instant rollback to prior **successful production** deployment | **YES** |
| Preview as rollback target | **NO** (production only) |
| API rollback | Available |

Meets Founder rollback expectation for edge deploys (complementary to local `output/website/` retention).

### 3.7 Provider lock-in

| Surface | Lock-in | Mitigation |
|---------|---------|------------|
| Content format | **Low** — plain HTML/XML | Re-point DNS + sync same public tree to Nginx/Caddy |
| Deploy workflow | **Medium** — Pages git/Wrangler/API | Keep Deployment Adapter host-agnostic; second adapter = self-host |
| DNS / nameservers (apex) | **Medium** if apex on Cloudflare | Prefer subdomain CNAME if DNS independence is priority |
| Edge features (`_headers`, Functions) | **Medium** if adopted | **Do not** require Functions for M5 static; avoid CF-only features in Core |

**Lock-in verdict:** Acceptable for first production provider because artifacts remain portable and Core stays host-agnostic.

### 3.8 Deployment adapter boundary

| Concern | Owner |
|---------|-------|
| Render / write `output/website/` | Website Engine Core + Static Provider |
| Public-subset packaging | Deployment Adapter (outside Core) |
| `wrangler pages deploy` / git push / Pages API | Deployment Adapter + Automation Platform |
| API tokens | Shared Platform secrets |
| Cloudflare project / DNS / TLS | Hosting ops (Cloudflare) — not Core |

---

## 4. Score vs M4 modes (provider lens)

Cloudflare Pages is a concrete instance of Scout’s **Git-backed / managed static** mode — not a CMS, not a Core provider.

| Dimension | Assessment vs self-hosted Nginx/Caddy |
|-----------|----------------------------------------|
| Ops burden | Lower (no OS/TLS patching) |
| HTTPS / CDN | Stronger default |
| Rollback UX | Stronger (one-click production rollback) |
| Preview | Stronger |
| Free cash cost | Comparable ($0 free tier) |
| Vendor coupling | Higher than bare metal OSS |
| Artifact fit | Equal (same public subset) |

---

## 5. Explicit non-actions (this evaluation)

- Does **not** create a Cloudflare account, Pages project, DNS record, or API token  
- Does **not** deploy `output/website/`  
- Does **not** modify Website Engine Core, Static Provider, Publishing, DB, or APIs  
- Does **not** purchase Pro/Business plans  

---

## 6. Recommendation

**CLOUDFLARE PAGES** is recommended as the **first production static deployment provider**, subject to:

1. Deployment Adapter outside Website Engine Core  
2. Public-subset packaging (HTML + sitemap + RSS; exclude `metadata.json` / `source.md`)  
3. Free plan first; no paid upgrade unless limits are hit  
4. Self-hosted Nginx/Caddy remains the **portable fallback** via the same adapter interface  
5. Human approval still gates production publish/deploy  

---

## FINAL

| Field | Value |
|-------|-------|
| **Recommended first production provider** | **CLOUDFLARE PAGES** |
| **Architecture chain** | Core → Deployment Adapter → Cloudflare Pages |
| **Provider Independent** | **YES** |
| **Paid required** | **NO** |
| **M4 deploy actions** | **NONE** |
