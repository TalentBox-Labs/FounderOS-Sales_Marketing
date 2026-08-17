# Website Deployment Runbook

**Module:** `src/tools/website_deployment/` (Deployment Adapter — M5)  
**Architecture:** Website Engine Core → Deployment Adapter → Cloudflare Pages / local static  
**Baselines:** Core v1.0 · Static Provider v1.0 · Publishing v1.0 (unchanged)  
**Staging RC:** **RC1 FROZEN** — [M6_5_RC1_BASELINE.md](M6_5_RC1_BASELINE.md)  
**Staging URL (RC1):** `https://preview.founderos-staging.pages.dev`  
**Production (M7):** `https://founderos-staging.pages.dev` — [M7_PRODUCTION_RELEASE.md](M7_PRODUCTION_RELEASE.md)  
**Branded DNS:** attach `blog.workcrew.ai` / `workcrew.ai` CNAMEs to `founderos-staging.pages.dev` (pending at M7).

### Production promote (RC1 → main)

```bash
set -a && source .env.local && set +a
wrangler pages deploy output/website-deploy/edge-upload/dep_m62_staging \
  --project-name="${CLOUDFLARE_PROJECT_NAME}" \
  --branch=main \
  --commit-dirty=true \
  --commit-message="M7 production cutover RC1"
```

---

## 1. Overview

The Deployment Adapter packages the **public subset** of Static Provider output and prepares host transport. It does **not** render Markdown, orchestrate Publishing jobs, or call Cloudflare automatically.

| Path | Purpose |
|------|---------|
| `output/website/` | Source artifacts (Static Provider v1.0) |
| `output/website-deploy/packages/{deployment_id}/` | Exported public package + manifest |
| `output/website-deploy/snapshots/{deployment_id}/` | Local rollback snapshot |
| `output/website-deploy/rollback-history.jsonl` | Rollback metadata append log |
| `output/website-deploy/cloudflare/` | Wrangler template + operator README |

**Public files:** `{slug}/index.html`, `sitemap.xml`, `rss.xml`  
**Excluded:** `metadata.json`, `source.md`

---

## 2. Prerequisites

1. Editorial approval + Publishing workflow (human gates) completed for production.  
2. Website artifacts present under `output/website/` (via `publish_content` / Static Provider).  
3. **Cloudflare (production):** account, Pages project, API token or `wrangler login` in secrets store — **not in repo**.  
4. **DNS / SSL:** custom domain or CNAME aligned with `canonical_url` in HTML/feeds.  
5. Python env: project `.venv` with FounderOS dependencies.

---

## 3. Export deployment package (operator)

```python
from pathlib import Path
from src.tools.website_deployment import DeploymentAdapter

adapter = DeploymentAdapter()
result = adapter.export_package()
print(result.deployment_id, result.package_root, result.ok)
```

Or from shell:

```bash
cd /Users/krishna/Documents/TB-FounderOS-Sales_Marketing
.venv/bin/python -c "
from src.tools.website_deployment import DeploymentAdapter
r = DeploymentAdapter().export_package()
print(r.to_dict())
"
```

Verify `deployment-manifest.json` inside the package directory and entries in `rollback-history.jsonl`.

---

## 4. Local deployment (Nginx/Caddy fallback)

```python
from pathlib import Path
from src.tools.website_deployment import DeploymentAdapter

adapter = DeploymentAdapter()
adapter.deploy_local(Path("/var/www/founder-site"))  # example docroot
```

Point Nginx/Caddy `root` at that directory. Ensure TLS termination matches production URLs.

---

## 5. Cloudflare Pages (primary — manual transport)

**Verified M6.2 staging project:** `founderos-staging` (preview branch).  
**Do not** attach production custom domains in staging retries.

1. Run **export** (§3).  
2. Build an **edge-safe** tree (HTML + `sitemap.xml` + `rss.xml` only — exclude `deployment-manifest.json`, `metadata.json`, `source.md`).  
3. Load credentials from a gitignored env file (names only in docs):

```bash
set -a && source .env.local && set +a
# expects: CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_PROJECT_NAME
```

4. Deploy Direct Upload:

```bash
wrangler pages deploy output/website-deploy/edge-upload/<deployment_id> \
  --project-name="${CLOUDFLARE_PROJECT_NAME}" \
  --branch=preview \
  --commit-dirty=true
```

5. Confirm staging URL (e.g. `https://preview.<project>.pages.dev`) over HTTPS.  
6. **Never** print or commit token values.

**Rollback (Cloudflare):** Dashboard → Deployments → Rollback to prior production deployment.  
**Rollback (local metadata):** Use `rollback-history.jsonl` + `snapshots/` to identify prior `deployment_id`, re-run local deploy or re-upload snapshot tree.

---

## 6. Environment configuration

| Variable | Where | Notes |
|----------|-------|-------|
| `CLOUDFLARE_API_TOKEN` | Shared Platform / CI secret | Optional; for Wrangler/API |
| `CLOUDFLARE_ACCOUNT_ID` | Shared Platform / CI secret | Optional |
| Pages project name | Adapter ctor / `prepare_cloudflare()` | Default `founder-website` |

Website Engine Core does **not** read these variables.

---

## 7. Verification checklist

- [ ] Public package excludes `metadata.json` and `source.md`  
- [ ] `sitemap.xml` and `rss.xml` present when feeds were generated  
- [ ] Manifest lists SHA-256 for each shipped file  
- [ ] Production DNS matches embedded canonical URLs  
- [ ] Publishing Engine was **not** used as deploy owner  

---

## 8. Troubleshooting

| Symptom | Action |
|---------|--------|
| Export fails — no public artifacts | Run Static Provider publish first |
| Wrong URLs on site | Fix DNS / custom domain; re-export after correcting `canonical_url` at source |
| Wrangler auth errors | Refresh token via Shared Platform secrets |
| Need prior version | Cloudflare rollback or redeploy from `snapshots/{deployment_id}` |

---

## 9. Boundaries (do not violate)

- Do not add deploy logic to `publishing_engine.py`.  
- Do not import Cloudflare SDKs from `src/tools/website_engine/`.  
- Do not commit API tokens or generated deploy trees with secrets.
