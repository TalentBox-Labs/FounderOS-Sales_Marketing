# M4 — Website Deployment Architecture

**Status:** DECIDED (architecture only)  
**Parent decision:** [M4_DEPLOYMENT_DECISION.md](M4_DEPLOYMENT_DECISION.md)  
**Architecture:** v2.2  
**Date:** 2026-08-10  

No runtime implementation in M4.

---

## 1. Layers

```text
Editorial Engine (human approve)
        ↓
Publishing Engine (orchestration only — jobs/queue/audit)
        ↓  (future: invoke website channel)
Website Engine Core (render + metadata + feeds)
        ↓
Static Provider (write output/website/)          ← FROZEN v1.0
        ↓
Deploy Layer (M5) — Website Engine hooks        ← OUTSIDE Core
        ↓
Static self-host (OSS web server + docroot)
```

| Layer | Owner | M4 status |
|-------|-------|-----------|
| Publishing orchestration | Hermes / Publishing Engine | Unchanged; no deploy |
| Core render/provider | Nova / Website Engine Core | FROZEN |
| Static filesystem publish | Nova / Static Provider | FROZEN |
| Deploy hooks + packaging | Nova / Website Engine (extensibility) | **Decided; not implemented** |
| Transport (optional later) | Automation Platform | Not required for manual sync M5 |
| Secrets / TLS certs ops | Shared Platform / ops | Outside Core |

---

## 2. Build artifact

| Item | Specification |
|------|----------------|
| **Primary artifact** | Static site tree |
| **Canonical directory** | `output/website/` |
| **Per-page** | `{slug}/index.html` (+ optional operator `metadata.json`, `source.md`) |
| **Site-level** | `sitemap.xml`, `rss.xml` |
| **Public subset (M5)** | Prefer HTML + sitemap + RSS for docroot; operator JSON/MD may be excluded from public serve |

---

## 3. Static serving (chosen mode)

**Mode:** Static self-host  

- Serve public subset from a Founder-controlled host using OSS static server (e.g. Caddy or nginx).  
- Sync via Website Engine deploy hook (rsync/scp-class) — **not** Publishing Engine.  
- No mandatory paid CDN.

**Secondary path:** Git-based hosting of the same public tree (automation convenience) without changing Core/Static contracts.

---

## 4. Non-functional requirements (decision targets)

| Concern | Decision target |
|---------|-----------------|
| HTTPS | Required for public site; terminate at self-host reverse proxy / ACME (OSS) |
| Custom domains | DNS A/AAAA or CNAME → self-host; must match `canonical_url` host |
| Cache | Server/`Cache-Control` at edge of static server; CDN optional later |
| CDN | Not required for M5; optional additive |
| Rollback | Keep prior published tree; redeploy previous package |
| Build pipeline | `publish_content` / Static Provider → package public subset → deploy hook → verify HTTPS |

---

## 5. Explicit non-ownership

| Must not own deploy | Why |
|---------------------|-----|
| Publishing Engine | Orchestration only (Hermes PASS) |
| Website Engine Core v1.0 contract | Deploy outside Core (Atlas PASS) |
| SEO / Social / Campaign Engines | Unrelated channels |
| Revenue OS | Different domain |

---

## 6. Future extensibility

```text
Static Provider (now)
    → Deploy hooks self-host / git-host (M5+)
    → Future WebsiteProvider: WordPress / Ghost (separate sprint)
```

Provider independence: **PASS** — hosting choice does not rewrite Static Provider interface.

---

## 7. Human gates

Production public exposure remains a **human-approved** Website Engine / Founder action.  
Editorial approval still does **not** authorize publish or deploy.
