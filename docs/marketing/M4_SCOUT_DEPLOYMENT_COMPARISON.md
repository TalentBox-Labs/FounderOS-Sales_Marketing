# M4 Scout — Deployment Model Comparison

**Role:** Agent Scout — Research (M4 analysis only)  
**Status:** ANALYSIS ONLY — **NO deploy · NO purchase · NO code**  
**Sprint:** M4  
**Date:** 2026-08-10  
**Owned file:** `docs/marketing/M4_SCOUT_DEPLOYMENT_COMPARISON.md` (this document only)  
**Canonical repository:** `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`  
**Architecture:** v2.1 ([Architecture_v2.1.md](../architecture/Architecture_v2.1.md), [Platform_vs_OS_Boundaries.md](../architecture/Platform_vs_OS_Boundaries.md))  
**Prerequisite evidence:** [M3_5_M4_DEPLOYMENT_READINESS.md](M3_5_M4_DEPLOYMENT_READINESS.md), [M3_STATIC_PROVIDER_REPORT.md](M3_STATIC_PROVIDER_REPORT.md), [M3_5_STATIC_PROVIDER_BASELINE.md](M3_5_STATIC_PROVIDER_BASELINE.md), [M2_5_WEBSITE_PROVIDER_READINESS.md](M2_5_WEBSITE_PROVIDER_READINESS.md)

**Mission constraint:** Prefer free / OSS / self-control. Do **not** recommend paid infrastructure unless technically required (justify if so).  
**Decision target:** Recommend **one** primary deployment model for the **M5 path**.

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

| Fact | Implication for deploy |
|------|------------------------|
| Artifact = directory tree | Best first consumers are file sync / static docroots, not CMS APIs |
| Public subset ≠ full tree | All modes need include/exclude rules (`index.html`, feeds in; `metadata.json` / `source.md` out or denied) |
| No root `index.html` today | Landing page is a content/engine gap, not a hosting-mode blocker |
| Feeds overwrite per publish | Aggregation is an engine concern; hosting mode does not fix it |
| Deploy ownership | **Website Engine** owns deploy hooks + cache invalidation; Automation may execute transport; Publishing stays orchestration-only |

---

## 2. Models evaluated

| ID | Name | One-line model |
|----|------|----------------|
| 1 | **Static self-host** | Serve public subset of `output/website/` with OSS static server (Caddy / nginx / Apache) on a host you control; sync via rsync/scp |
| 2 | **Git-based hosting** | Publish filtered public tree to a git branch/repo that a Pages-style host serves as static files |
| 3 | **Managed static hosting** | Upload/sync public tree to a managed static/object+CDN edge |
| 4 | **Container deployment** | `COPY` public subset into an image with nginx/Caddy; run on a container host |
| 5 | **Future CMS adapters** | WordPress / Ghost (or similar) as later `WebsiteProvider` destinations; static tree becomes staging/audit, not primary public docroot |

---

## 3. Comparison dimensions

Scoring: **5** = best fit for FounderOS M5 under free/OSS/self-control · **3** = workable · **1** = poor first path.

### 3.1 Cost

| Mode | Score | Assessment |
|------|------:|------------|
| Static self-host | **5** | Free OSS stack (Caddy/nginx, Let’s Encrypt). May use an already-owned VPS/home lab; **no new paid product required**. If no host exists, a single always-on machine is an ops cost, not a SaaS bill. |
| Git-based hosting | **4** | Free tiers common (e.g. Pages-style flows). Cost is usually $0 at Founder scale; risk is soft lock into a free-tier host policy, not an invoice. |
| Managed static hosting | **2** | Free tiers exist but **paid creep** (bandwidth, build minutes, team seats, custom domains on some plans) is the failure mode M2.5 explicitly avoided. Not technically required for static HTML. |
| Container deployment | **3** | OSS runtime free; registry + always-on compute still needed. Extra machinery without lowering cash cost vs plain static serve. |
| Future CMS adapters | **1** | Self-hosted WP/Ghost are OSS, but DB + app hosting + updates dominate cost/effort vs static files. Paid CMS SaaS is explicitly out of preference. |

**Paid infrastructure required?** **No.** Static HTML from M3 does not technically require a paid CDN, paid static host, or paid CMS. Free/OSS self-host (or free git Pages) is sufficient for first public reachability.

---

### 3.2 Complexity

| Mode | Score | Assessment |
|------|------:|------------|
| Static self-host | **4** | Mental model matches artifacts 1:1: filter → rsync → docroot. Complexity is TLS/DNS/uptime (operator), not adapter translation. |
| Git-based hosting | **3** | Needs public-subset packaging + “do we commit generated HTML?” policy + deploy token hygiene. Host hides TLS; git workflow adds process complexity. |
| Managed static hosting | **3** | CLI/API sync is simple once chosen; provider-agnostic hook + secrets + invalidation semantics add decision surface. |
| Container deployment | **2** | Dockerfile, registry, rollouts, ingress — disproportionate for brochure/blog static files. |
| Future CMS adapters | **1** | Highest: auth, content-model mapping, theme/SEO plugin duplication, `external_http=True`, DB ops. Deferred by M2.5/M3 by design. |

---

### 3.3 Vendor lock-in

| Mode | Score | Assessment |
|------|------:|------------|
| Static self-host | **5** | Files + OSS server. Move host by re-rsync. No proprietary build API. |
| Git-based hosting | **3** | Artifact remains plain files (good), but DNS/Pages/workflow couple to a git host. Exit = point DNS + copy tree elsewhere. |
| Managed static hosting | **2** | Deploy CLI, env vars, CDN purge APIs, and free-tier limits create stickiness even if HTML is portable. |
| Container deployment | **4** | Image is portable across runtimes; lock-in risk is orchestration platform habit, not content format. |
| Future CMS adapters | **1** | Content/theme/plugin/DB captivity; fights Website Engine as canonical render owner unless carefully publishing pre-rendered HTML. |

---

### 3.4 Maintenance

| Mode | Score | Assessment |
|------|------:|------------|
| Static self-host | **3** | You own OS updates, TLS renewals (Caddy eases this), backups, firewall. Medium for solo founder; predictable. |
| Git-based hosting | **4** | Less server patching; more branch/policy hygiene and generated-artifact noise in git. |
| Managed static hosting | **4** | Host patches the edge; you maintain tokens, billing vigilance, and deploy config. |
| Container deployment | **2** | Image base updates + registry + runtime patching — more moving parts than the site content warrants. |
| Future CMS adapters | **1** | Continuous CMS/core/plugin/DB maintenance; security surface far above static files. |

---

### 3.5 Automation

| Mode | Score | Assessment |
|------|------:|------------|
| Static self-host | **4** | Natural Website Engine deploy hook: package public subset → rsync/scp. Automation Platform can own transport; secrets = SSH keys in Shared Platform. Manual rsync acceptable for M5 first cut. |
| Git-based hosting | **5** | Strong CI fit (generate → commit/push or artifact upload). Rollback via git history. Requires clear “generated HTML” policy. |
| Managed static hosting | **5** | Strong CI/CLI sync once hook exists; invalidation often = redeploy. |
| Container deployment | **4** | Standard image pipeline; heavier than file sync for the same HTML. |
| Future CMS adapters | **3** | API publish at approval time is automatable, but adapter + idempotent update-by-slug is large net-new work. |

---

### 3.6 Scalability

| Mode | Score | Assessment |
|------|------:|------------|
| Static self-host | **3** | Fine for Founder brochure/blog traffic; scale-up = bigger box or optional free/cheap reverse-proxy cache later. Not a global CDN by default. |
| Git-based hosting | **4** | Host edge usually absorbs traffic spikes at Founder scale without Founder ops. |
| Managed static hosting | **5** | Best raw edge scale — **not needed** until traffic or global latency proves it. |
| Container deployment | **3** | Horizontal scale possible; overkill before single-node static fails. |
| Future CMS adapters | **2** | App+DB scales worse than static files for the same content; caching layers re-introduce complexity Website Engine already owns in principle. |

**Note:** Current artifact volume (per-slug HTML + feeds) does **not** create a technical requirement for managed CDN scale in M5.

---

## 4. Scoreboard

| Dimension (weight toward free/OSS control) | Static self-host | Git-based | Managed static | Container | Future CMS |
|--------------------------------------------|-----------------:|----------:|---------------:|----------:|-----------:|
| Cost | 5 | 4 | 2 | 3 | 1 |
| Complexity | 4 | 3 | 3 | 2 | 1 |
| Vendor lock-in | 5 | 3 | 2 | 4 | 1 |
| Maintenance | 3 | 4 | 4 | 2 | 1 |
| Automation | 4 | 5 | 5 | 4 | 3 |
| Scalability | 3 | 4 | 5 | 3 | 2 |
| **Total** | **24** | **23** | **21** | **18** | **9** |

| Rank | Mode | M5 fitness |
|-----:|------|------------|
| 1 | **Static self-host** | **Primary** — direct artifact fit, max control, $0 product path |
| 2 | Git-based hosting | Strong secondary / later automation upgrade on free tiers |
| 3 | Managed static hosting | Viable only if already-owned or strictly free; do not select paid vendor for M5 |
| 4 | Container deployment | Optional if containers are already mandatory elsewhere; not first static cut |
| 5 | Future CMS adapters | Deferred after static public path is proven (M2.5/M3/M3.5 consistent) |

---

## 5. Cross-mode requirements (unchanged by recommendation)

Regardless of primary mode, M5 must still respect:

1. **Public-subset packaging** — expose `{slug}/index.html`, `sitemap.xml`, `rss.xml`; exclude or deny `metadata.json` / `source.md`.
2. **Website Engine deploy hook** — owner of site deploy + cache invalidation (v2.1); unimplemented today.
3. **Automation Platform** — may execute transport; no business logic ownership of the site.
4. **Shared Platform** — holds SSH keys / deploy tokens; never bake secrets into repo or HTML.
5. **Publishing Engine** — orchestration / gates only; does **not** own docroots or CDN.
6. **Human approval gate** — deploy must not bypass Editorial/Publishing production gates.
7. **Canonical URL ↔ DNS** — public host must match URLs already embedded in HTML/feeds.
8. **No paid provider selection in architecture** — keep hook transport-agnostic (rsync first).

---

## 6. M5 path implication (primary mode)

If **Static self-host** is primary, M5 work stays narrow and free/OSS:

| M5 slice | Intent |
|----------|--------|
| Public artifact package | Filter rules from `output/website/` |
| Minimal deploy hook | Website Engine interface → sync public tree (e.g. rsync/scp mental model; host-agnostic) |
| Serve topology | OSS static server + TLS (Caddy recommended mentally for auto-HTTPS; nginx equally valid) |
| Runbook | DNS, rollback via prior docroot snapshot, exclude operator files |
| Explicit non-goals | Paid CDN/SaaS selection, WP/Ghost adapters, Publishing ownership of hosting, container registry mandate |

**Secondary path (not primary):** Git-based hosting remains the best free automation upgrade once public-subset packaging and “derived HTML” git policy are frozen — without changing Website Engine render ownership.

---

## 7. Explicit non-actions (this scout)

- Does **not** deploy, sync, or expose any site.
- Does **not** purchase or recommend a paid host/CDN/CMS plan.
- Does **not** choose Netlify / Vercel / Cloudflare / AWS / etc. as required vendors.
- Does **not** implement hooks, Dockerfiles, nginx configs, or CI.
- Does **not** authorize WordPress/Ghost adapters for M5.

---

## 8. Attestation

| Item | Value |
|------|-------|
| Analysis file | `docs/marketing/M4_SCOUT_DEPLOYMENT_COMPARISON.md` |
| Code / infra / spend | **NONE** |
| Paid infrastructure recommended | **NO** (not technically required) |
| Artifact basis | M3 `output/website/` static contract |
| Preference applied | Free / OSS / self-control |
| Confidence | **HIGH** — grounded in frozen Static Provider contract + M3.5 readiness + M2.5 no-paid-SaaS constraint |

---

## FINAL

**Recommended Mode:** Static self-host

**Rationale:** M3 already emits a filesystem publication surface under `output/website/`; the lowest-cost, lowest-lock-in M5 path is to package the public subset and serve it with an OSS static server (Caddy/nginx) behind a Website Engine deploy hook (rsync/scp-class sync), keeping render ownership, secrets, and rollback under Founder control without paying for CDN/CMS products that static HTML does not require. Git-based hosting is the nearest free secondary for CI convenience; managed hosts, containers, and CMS adapters add cost, lock-in, or complexity without unlocking a capability the current artifact set lacks.
