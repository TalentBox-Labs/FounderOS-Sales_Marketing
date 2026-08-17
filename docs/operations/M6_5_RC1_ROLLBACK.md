# M6.5 — RC1 Rollback Evidence

**Release Candidate:** RC1  
**Artifact:** `dep_m62_staging`  
**Staging project:** `founderos-staging` / branch `preview`  

---

## Local rollback

1. Prior package/snapshot: `output/website-deploy/snapshots/dep_m62_staging/`  
2. Re-upload edge-safe tree via Wrangler Direct Upload, or  
3. `DeploymentAdapter.deploy_local(docroot, deployment_id="dep_m62_staging", export_first=False)` for Nginx/Caddy fallback  

History: `output/website-deploy/rollback-history.jsonl`

---

## Cloudflare rollback

1. Cloudflare dashboard → Workers & Pages → `founderos-staging` → Deployments  
2. Select prior successful **preview** deployment (RC1: `a4d3550c…`)  
3. Rollback / redeploy as needed — **do not** attach production domains  

---

## Classification

**ROLLBACK: READY**
