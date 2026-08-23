# M7.5 — Release & Rollback Ledger

**Agent:** Ledger  
**Sprint:** M7.5  
**Date:** 2026-08-10  

---

## Production release record

| Item | Value |
|------|-------|
| Product | Founder OS Website |
| Version | **v1.0** |
| Release identifier | **RC1 → Production** |
| Git SHA | `e1efc0892ea13dad856b952110c7cc38d24565c3` |
| Branch | `develop` |
| Artifact ID | `dep_m62_staging` |
| Artifact checksum (page) | `42c95071ba79d9b0a7b4771d2aebaebd69ca7ce015dd1ee6c6c5818e6e9b1d47` |
| Deployment ID | `80d03643-e871-4a28-bf74-376014301a12` |
| Production URL | `https://founderos-staging.pages.dev` |
| Release timestamp | 2026-08-10 (M7 cutover) |
| Last known good | Same deployment (`80d03643…`) / RC1 snapshot |
| Rollback target | Prior Cloudflare Production deployment **or** re-upload `edge-upload/dep_m62_staging` / snapshot |
| Historical regression | **327/339**; 8 failed; 4 errors; 0 new (M7.5 reconfirm) |

---

## Rollback procedure (do not execute)

1. Cloudflare → Workers & Pages → `founderos-staging` → Deployments → Production → rollback/redeploy prior.  
2. Or: `wrangler pages deploy output/website-deploy/edge-upload/dep_m62_staging --project-name=founderos-staging --branch=main`  
3. Local fallback: `DeploymentAdapter.deploy_local(...)` with snapshot `dep_m62_staging`.

**Rollback: READY** (actionable; not intentionally triggered)
