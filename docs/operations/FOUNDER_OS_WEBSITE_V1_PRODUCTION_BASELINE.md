# Founder OS Website v1.0 — Production Baseline

**Status:** **FROZEN**  
**Sprint:** M7.5  
**Date:** 2026-08-10  

---

| Field | Value |
|-------|-------|
| **Product** | Founder OS Website |
| **Version** | **v1.0** |
| **Environment** | **PRODUCTION** |
| **Hosting** | Cloudflare Pages |
| **Architecture** | **v2.2** |
| **Release Candidate** | **RC1** (`dep_m62_staging`) |
| **Production URL** | `https://founderos-staging.pages.dev` |
| **Git SHA** | `e1efc0892ea13dad856b952110c7cc38d24565c3` |
| **Artifact Checksum** | `42c95071ba79d9b0a7b4771d2aebaebd69ca7ce015dd1ee6c6c5818e6e9b1d47` (`hiring-systems/index.html`) |
| **Deployment ID** | `80d03643-e871-4a28-bf74-376014301a12` |
| **Security** | **PASS** |
| **Publishing** | **PASS** |
| **Rollback** | **READY** |
| **Regression** | **PASS** (65/65 focused; 327/339 full; 0 new) |
| **Architecture** | **PASS** |
| **Status** | **FROZEN** |

---

## Evidence pack

| Agent | Document |
|-------|----------|
| Nova | [M7_5_PRODUCTION_DEPLOYMENT_EVIDENCE.md](M7_5_PRODUCTION_DEPLOYMENT_EVIDENCE.md) |
| Sentinel | [M7_5_PRODUCTION_SMOKE_TEST.md](M7_5_PRODUCTION_SMOKE_TEST.md) |
| Cipher | [M7_5_PRODUCTION_SECURITY.md](M7_5_PRODUCTION_SECURITY.md) |
| Hermes | [M7_5_PUBLISHING_CERTIFICATION.md](M7_5_PUBLISHING_CERTIFICATION.md) |
| Atlas | [M7_5_ARCHITECTURE_CERTIFICATION.md](M7_5_ARCHITECTURE_CERTIFICATION.md) |
| Ledger | [M7_5_RELEASE_LEDGER.md](M7_5_RELEASE_LEDGER.md) |
| Prior cutover | [M7_PRODUCTION_RELEASE.md](M7_PRODUCTION_RELEASE.md) |
| RC1 freeze | [M6_5_RC1_BASELINE.md](M6_5_RC1_BASELINE.md) |

---

## Known frozen limitations (not freeze blockers)

1. Root `/` returns 404 (no landing page in Static v1.0).  
2. Branded domains `workcrew.ai` / `blog.workcrew.ai` attached but **DNS CNAME pending** — not the certified URL.  
3. Publishing website channel remains PLACEHOLDER for auto-invoke; production used RC1 static + Deployment Adapter path.  
4. Project slug remains `founderos-staging` while serving Production branch.

---

## Cross-agent conflicts

**0**

---

## Verdict

**FOUNDER OS WEBSITE v1.0 PRODUCTION BASELINE FROZEN**
