# M5 — Deployment Governance (Ledger)

**Agent:** Ledger — Governance  
**Sprint:** M5 — Website Deployment Implementation  
**Date:** 2026-08-10

---

## 1. Deployment checklist (pre-export)

- [ ] Editorial approval recorded for content being published  
- [ ] Publishing job completed or Static publish run under human gate  
- [ ] `output/website/` contains expected slugs and feeds  
- [ ] `canonical_url` values match intended production host  
- [ ] No secrets in artifact tree  

---

## 2. Release checklist (production edge)

- [ ] `DeploymentAdapter.export_package()` succeeded  
- [ ] Manifest + rollback history written  
- [ ] Public subset verified (no `metadata.json` / `source.md` on edge)  
- [ ] Cloudflare Pages deploy OR local docroot sync completed by operator  
- [ ] HTTPS valid on custom domain  
- [ ] Sample pages and feeds load correctly  

---

## 3. Rollback procedure

**Cloudflare Pages**

1. Open Pages project → Deployments.  
2. Select last known-good **production** deployment.  
3. Rollback to that deployment (instant).  

**Local / adapter metadata**

1. Read `output/website-deploy/rollback-history.jsonl` for prior `deployment_id`.  
2. Use `output/website-deploy/snapshots/{deployment_id}/` as source tree.  
3. Re-run `deploy_local()` or manual Wrangler upload from snapshot.  

---

## 4. Environment configuration

| Item | Owner | Storage |
|------|-------|---------|
| Cloudflare API token | Shared Platform | Secret manager / CI vars |
| Account ID | Shared Platform | Secret manager |
| Pages project name | Ops config | Adapter default or parameter |
| Local docroot path | Ops | Server config |

---

## 5. Domain preparation

- Choose apex or subdomain consistent with Website Engine `canonical_url`.  
- Subdomain: CNAME to `{project}.pages.dev`.  
- Apex: domain as Cloudflare zone recommended for automatic TLS.  

---

## 6. DNS requirements

| Pattern | Record |
|---------|--------|
| Subdomain blog | CNAME → Pages subdomain |
| Apex | Cloudflare zone + automatic records OR documented CNAME flattening |

---

## 7. SSL requirements

- Cloudflare Pages: automatic certificates on `*.pages.dev` and attached custom domains.  
- Self-hosted fallback: Caddy auto-HTTPS or Nginx + Let's Encrypt.  
- Resolve CAA records if certificate issuance fails (allow Cloudflare CAs).  

---

## Verdict

**Governance: PASS** — Checklists documented; human gates unchanged.
