# M4 Scout — Deployment Options

**Role:** Agent Scout — Deployment Research (M4)  
**Status:** ANALYSIS ONLY — **NO deploy · NO purchase · NO code**  
**Sprint:** M4  
**Date:** 2026-08-10  
**Owned file:** `docs/marketing/M4_DEPLOYMENT_OPTIONS.md` (this document only)  
**Canonical repository:** `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`  
**Architecture:** v2.1 / v2.2 ([Architecture_v2.1.md](../architecture/Architecture_v2.1.md), [Platform_vs_OS_Boundaries.md](../architecture/Platform_vs_OS_Boundaries.md))  
**Prerequisite evidence:** [M3_5_M4_DEPLOYMENT_READINESS.md](M3_5_M4_DEPLOYMENT_READINESS.md), [M3_STATIC_PROVIDER_REPORT.md](M3_STATIC_PROVIDER_REPORT.md), [M4_SCOUT_DEPLOYMENT_COMPARISON.md](M4_SCOUT_DEPLOYMENT_COMPARISON.md)

**Mission constraint:** Prefer free / OSS / self-control. Do **not** recommend paid infrastructure unless technically required.  
**Decision target:** Recommend **one** primary deployment model for the M5 path.

**Scope note:** Managed/paid static SaaS hosts are **out of scope** for this options brief (see sibling Scout comparison for that track). This document compares only the four modes below.

---

## 1. Artifact under comparison

Website Engine `StaticWebsiteProvider` (`name=static`) writes a local filesystem tree (default `output/website/`). There is **no** deploy hook, CDN, or network publish today (`external_http=False`).

```text
output/website/
├── {slug}/
│   ├── index.html      ← public page (directory URL /{slug}/)
│   ├── metadata.json   ← operator/debug; typically NOT public
│   └── source.md       ← source archive; typically NOT public
├── sitemap.xml         ← public feed
└── rss.xml             ← public feed
```

| Fact | Implication |
|------|-------------|
| Artifact = directory tree | Best first consumers are file sync / static docroots, not CMS APIs |
| Public subset ≠ full tree | All modes need include/exclude rules (`index.html`, feeds in; `metadata.json` / `source.md` out or denied) |
| Deploy ownership | **Website Engine** owns deploy hooks + cache invalidation; Automation may execute transport; Publishing stays orchestration-only |

---

## 2. Models evaluated

| ID | Name | One-line model |
|----|------|----------------|
| 1 | **Self-hosted static server (Nginx/Caddy)** | Serve public subset of `output/website/` with OSS Nginx or Caddy on a host you control; sync via rsync/scp |
| 2 | **Git-backed static hosting** | Publish filtered public tree to a git branch/repo that a Pages-style host serves as static files |
| 3 | **Containerized static deployment** | `COPY` public subset into an image with Nginx/Caddy; run on a container host |
| 4 | **Future CMS adapter** | WordPress / Ghost (or similar) as later `WebsiteProvider` destinations; static tree becomes staging/audit, not primary public docroot |

---

## 3. Evaluation dimensions

Scoring: **5** = best fit for FounderOS M5 under free/OSS/self-control · **3** = workable · **1** = poor first path.

### 3.1 Operational complexity

| Mode | Score | Assessment |
|------|------:|------------|
| Self-hosted static (Nginx/Caddy) | **4** | Mental model matches artifacts 1:1: filter → rsync → docroot. Ops load is DNS/TLS/uptime, not content translation. |
| Git-backed static hosting | **3** | Needs public-subset packaging + “commit generated HTML?” policy + deploy-token hygiene. Host hides TLS; git workflow adds process surface. |
| Containerized static | **2** | Dockerfile, registry, rollouts, ingress — disproportionate for brochure/blog static files. |
| Future CMS adapter | **1** | Highest: auth, content-model mapping, theme/SEO plugin duplication, `external_http=True`, DB ops. Deferred by M2.5/M3 by design. |

### 3.2 Rollback

| Mode | Score | Assessment |
|------|------:|------------|
| Self-hosted static (Nginx/Caddy) | **4** | Prior docroot snapshot / rsync backup → restore previous tree. Operator-owned, immediate, no vendor API. |
| Git-backed static hosting | **5** | `git revert` / redeploy previous commit — clearest history-native rollback. |
| Containerized static | **4** | Previous image tag/digest roll-back; solid if tags are immutable and registry retained. |
| Future CMS adapter | **2** | CMS revisions / DB backup — weaker and slower than static file revert; risk of partial content drift. |

### 3.3 Security

| Mode | Score | Assessment |
|------|------:|------------|
| Self-hosted static (Nginx/Caddy) | **4** | Small attack surface (static files only). You own OS hardening, firewall, SSH keys (Shared Platform). Must deny operator files in docroot. |
| Git-backed static hosting | **3** | Static edge is safe; risk shifts to deploy tokens, branch protection, and accidental commit of secrets/`metadata.json`/`source.md`. |
| Containerized static | **3** | Same static surface plus registry/runtime supply chain and base-image patching. |
| Future CMS adapter | **1** | App + DB + auth + plugins — continuous CVE/update surface far above static HTML. |

### 3.4 HTTPS

| Mode | Score | Assessment |
|------|------:|------------|
| Self-hosted static (Nginx/Caddy) | **4** | Operator-managed. **Caddy** auto-HTTPS (Let’s Encrypt) is the lowest-friction OSS path; Nginx + certbot equally valid. |
| Git-backed static hosting | **5** | Typically host-provided TLS with near-zero Founder cert ops. |
| Containerized static | **3** | TLS usually at ingress/reverse proxy — extra layer vs bare Caddy on the host. |
| Future CMS adapter | **3** | Depends on CMS host stack; not simpler than static for first cut. |

### 3.5 Custom domains

| Mode | Score | Assessment |
|------|------:|------------|
| Self-hosted static (Nginx/Caddy) | **5** | Full DNS control → host; must align with Website Engine `canonical_url`. No vendor domain gating. |
| Git-backed static hosting | **4** | Host DNS instructions; free tiers usually allow custom domains; policy/vendor UX varies. |
| Containerized static | **4** | Ingress host rules + DNS; portable but more config than a single Caddy `site` block. |
| Future CMS adapter | **3** | Domain binding via CMS host; fine later, irrelevant advantage for M5 static. |

### 3.6 CI/CD friendliness

| Mode | Score | Assessment |
|------|------:|------------|
| Self-hosted static (Nginx/Caddy) | **4** | Natural Website Engine deploy hook: package public subset → rsync/scp. Manual sync acceptable for M5 first cut; Automation can own transport later. |
| Git-backed static hosting | **5** | Strongest CI fit (generate → commit/push or artifact upload). Requires clear derived-HTML git policy. |
| Containerized static | **4** | Standard image pipeline; heavier than file sync for the same HTML. |
| Future CMS adapter | **3** | API publish at approval time is automatable, but adapter + idempotent update-by-slug is large net-new work. |

### 3.7 Maintenance

| Mode | Score | Assessment |
|------|------:|------------|
| Self-hosted static (Nginx/Caddy) | **3** | You own OS updates, TLS renewals (Caddy eases this), backups, firewall. Medium for solo founder; predictable. |
| Git-backed static hosting | **4** | Less server patching; more branch/policy hygiene and generated-artifact noise in git. |
| Containerized static | **2** | Image base updates + registry + runtime patching — more moving parts than the site content warrants. |
| Future CMS adapter | **1** | Continuous CMS/core/plugin/DB maintenance. |

### 3.8 Scalability

| Mode | Score | Assessment |
|------|------:|------------|
| Self-hosted static (Nginx/Caddy) | **3** | Fine for Founder brochure/blog traffic; scale-up = bigger box or optional reverse-proxy cache later. Not a global CDN by default. |
| Git-backed static hosting | **4** | Host edge usually absorbs Founder-scale spikes without Founder ops. |
| Containerized static | **3** | Horizontal scale possible; overkill before single-node static fails. |
| Future CMS adapter | **2** | App+DB scales worse than static files for the same content. |

**Note:** Current artifact volume does **not** create a technical requirement for paid CDN scale in M5.

### 3.9 Free / OSS suitability

| Mode | Score | Assessment |
|------|------:|------------|
| Self-hosted static (Nginx/Caddy) | **5** | Free OSS stack (Nginx/Caddy, Let’s Encrypt). May use an already-owned host; **no new paid product required**. |
| Git-backed static hosting | **4** | Free tiers common (Pages-style). Cost usually $0 at Founder scale; soft lock into free-tier host policy is the main risk. |
| Containerized static | **3** | OSS runtime free; registry + always-on compute still needed. Extra machinery without lowering cash cost vs plain static serve. |
| Future CMS adapter | **1** | Self-hosted WP/Ghost are OSS, but DB + app hosting + updates dominate cost/effort vs static files. |

**Paid infrastructure required?** **No.** Static HTML from M3 does not technically require a paid CDN, paid static host, or paid CMS.

### 3.10 Vendor lock-in

| Mode | Score | Assessment |
|------|------:|------------|
| Self-hosted static (Nginx/Caddy) | **5** | Files + OSS server. Move host by re-rsync. No proprietary build API. |
| Git-backed static hosting | **3** | Artifact remains plain files (good), but DNS/Pages/workflow couple to a git host. Exit = point DNS + copy tree elsewhere. |
| Containerized static | **4** | Image is portable across runtimes; lock-in risk is orchestration habit, not content format. |
| Future CMS adapter | **1** | Content/theme/plugin/DB captivity; fights Website Engine as canonical render owner unless carefully publishing pre-rendered HTML. |

---

## 4. Scoreboard

| Dimension | Self-hosted Nginx/Caddy | Git-backed | Containerized | Future CMS |
|-----------|------------------------:|-----------:|--------------:|-----------:|
| Operational complexity | 4 | 3 | 2 | 1 |
| Rollback | 4 | 5 | 4 | 2 |
| Security | 4 | 3 | 3 | 1 |
| HTTPS | 4 | 5 | 3 | 3 |
| Custom domains | 5 | 4 | 4 | 3 |
| CI/CD friendliness | 4 | 5 | 4 | 3 |
| Maintenance | 3 | 4 | 2 | 1 |
| Scalability | 3 | 4 | 3 | 2 |
| Free / OSS suitability | 5 | 4 | 3 | 1 |
| Vendor lock-in | 5 | 3 | 4 | 1 |
| **Total** | **41** | **40** | **32** | **18** |

| Rank | Mode | M5 fitness |
|-----:|------|------------|
| 1 | **Self-hosted static server (Nginx/Caddy)** | **Primary** — direct artifact fit, max control, $0 product path |
| 2 | Git-backed static hosting | Strong secondary / later automation upgrade on free tiers |
| 3 | Containerized static deployment | Optional if containers are already mandatory elsewhere; not first static cut |
| 4 | Future CMS adapter | Deferred after static public path is proven (M2.5/M3/M3.5 consistent) |

---

## 5. Per-model summary

### 1. Self-hosted static server (Nginx/Caddy)

| Aspect | Verdict |
|--------|---------|
| Fit to `output/website/` | Direct — sync public subset to docroot |
| Best for | First public reachability, Founder control, teaching Website Engine deploy hooks |
| Watch-outs | Always-on host, OS/TLS/firewall ownership, public-subset deny rules |

### 2. Git-backed static hosting

| Aspect | Verdict |
|--------|---------|
| Fit to `output/website/` | High after filter/package step |
| Best for | CI convenience and history-native rollback without owning a web server |
| Watch-outs | Generated-HTML git policy; deploy tokens; soft host coupling |

### 3. Containerized static deployment

| Aspect | Verdict |
|--------|---------|
| Fit to `output/website/` | Same files, heavier packaging (`COPY` into image) |
| Best for | Orgs already standardized on containers for every surface |
| Watch-outs | Registry, image churn, ingress — overkill for first brochure/blog cut |

### 4. Future CMS adapter

| Aspect | Verdict |
|--------|---------|
| Fit to `output/website/` | Weak as **primary** public docroot; tree becomes staging/audit |
| Best for | Later WordPress/Ghost provider work behind the same protocol |
| Watch-outs | Render ownership split, DB/security surface, not M5 first path |

---

## 6. Cross-mode requirements (unchanged by recommendation)

Regardless of primary mode, M5 must still respect:

1. **Public-subset packaging** — expose `{slug}/index.html`, `sitemap.xml`, `rss.xml`; exclude or deny `metadata.json` / `source.md`.
2. **Website Engine deploy hook** — owner of site deploy + cache invalidation (v2.1); unimplemented today.
3. **Automation Platform** — may execute transport; no business logic ownership of the site.
4. **Shared Platform** — holds SSH keys / deploy tokens; never bake secrets into repo or HTML.
5. **Publishing Engine** — orchestration / gates only; does **not** own docroots or CDN.
6. **Human approval gate** — deploy must not bypass Editorial/Publishing production gates.
7. **Canonical URL ↔ DNS** — public host must match URLs already embedded in HTML/feeds.
8. **No paid provider selection in architecture** — keep hook transport-agnostic (rsync-class first).

---

## 7. Explicit non-actions (this scout)

- Does **not** deploy, sync, or expose any site.
- Does **not** purchase or recommend a paid host/CDN/CMS plan.
- Does **not** choose Netlify / Vercel / Cloudflare / AWS / etc. as required vendors.
- Does **not** implement hooks, Dockerfiles, Nginx/Caddy configs, or CI.
- Does **not** authorize WordPress/Ghost adapters for M5.

---

## 8. Attestation

| Item | Value |
|------|-------|
| Analysis file | `docs/marketing/M4_DEPLOYMENT_OPTIONS.md` |
| Code / infra / spend | **NONE** |
| Paid infrastructure recommended | **NO** (not technically required) |
| Artifact basis | M3 `output/website/` static contract |
| Preference applied | Free / OSS / self-control |
| Models compared | 4 (self-host Nginx/Caddy · git-backed · containerized · future CMS) |
| Confidence | **HIGH** — grounded in frozen Static Provider contract + M3.5 readiness + prior Scout ranking |

---

## FINAL

**Recommended Model:** Self-hosted static server (Nginx/Caddy)

**Rationale:** M3 already emits a filesystem tree under `output/website/`; the lowest-cost, lowest-lock-in M5 path is to package the public subset and serve it with OSS Nginx/Caddy (Caddy preferred mentally for auto-HTTPS) behind a Website Engine rsync/scp-class deploy hook—keeping render ownership, secrets, and rollback under Founder control without paying for CDN/CMS that static HTML does not require. Git-backed hosting is the nearest free secondary for CI convenience; containers and CMS adapters add complexity or captivity without unlocking a missing artifact capability.
