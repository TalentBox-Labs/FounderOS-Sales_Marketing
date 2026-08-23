# M7.5 — Production Deployment Evidence (Nova)

**Agent:** Nova  
**Sprint:** M7.5  
**Date:** 2026-08-10  
**Code / deploy changes this sprint:** **NONE**

---

## Actual production deployment

| Field | Verified value |
|-------|----------------|
| Production URL | `https://founderos-staging.pages.dev` |
| Deployment URL | `https://80d03643.founderos-staging.pages.dev` |
| Cloudflare project | `founderos-staging` |
| Production branch / environment | `main` / **Production** |
| Cloudflare deployment ID | `80d03643-e871-4a28-bf74-376014301a12` |
| Deployed artifact / package ID | **RC1** · `dep_m62_staging` |
| Manifest created_at | `2026-08-10T12:24:38+00:00` |
| Repository branch | `develop` |
| Git HEAD SHA | `e1efc0892ea13dad856b952110c7cc38d24565c3` |

---

## Artifact checksums (RC1)

| Path | SHA-256 |
|------|---------|
| `hiring-systems/index.html` | `42c95071ba79d9b0a7b4771d2aebaebd69ca7ce015dd1ee6c6c5818e6e9b1d47` |
| `rss.xml` | `2927adcd64c76166dd15c60039394eafb24e721aa193467d9229f24cace99ee0` |
| `sitemap.xml` | `156e5e4c1c09f033b02e981c1a4322bfb1c7b1c3f47025056d6fbd0599aa3805` |

---

## RC1 equivalence proof

| Check | Result |
|-------|--------|
| Local edge tree matches RC1 manifest hashes | **PASS** |
| Live production `/hiring-systems/` SHA-256 | `42c95071ba79d9b0a7b4771d2aebaebd69ca7ce015dd1ee6c6c5818e6e9b1d47` |
| Live staging preview page SHA-256 | **identical** |
| Production ↔ RC1 edge HTML | **PASS** (byte-identical) |
| Wrangler production deployment present | **PASS** (`80d03643…`, Environment=Production) |

**Artifact Match: PASS** — production serves approved RC1.

---

## Custom domains (informational)

| Domain | Status |
|--------|--------|
| `blog.workcrew.ai` | Attached · DNS **pending** (CNAME not set) |
| `workcrew.ai` | Attached · DNS **pending** (CNAME not set) |

Branded hostnames are **not** the certified production URL for this freeze. Certified production URL remains `https://founderos-staging.pages.dev`.
