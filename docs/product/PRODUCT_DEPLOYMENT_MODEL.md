# Product Deployment Model

**Sprint:** MDG0  
**Date:** 2026-08-13  
**Mode:** AUDIT ONLY

## Critical distinction

| Surface | What | Host |
|---------|------|------|
| **PUBLIC WEBSITE** | Static `output/website/` | Cloudflare Pages (decided M4); Nginx/Caddy fallback |
| **FOUNDER OS APPLICATION** | FastAPI + Jinja (+ optional `/app`) | Local / Docker Compose / Render / Railway |

**Public Website and Founder OS App: SEPARATE_APPLICATIONS**

Cloudflare currently hosts the **static public website**, not the FastAPI application.

Do not conflate Website Engine output with the Founder OS Jinja shell (`/cockpit`, `/operator`).

## Application deployment readiness

**STAGING_READY** (with INTERNAL characteristics)

| Dimension | State |
|-----------|-------|
| Local development | YES |
| Internal / private host | YES (Docker / VPS blueprint) |
| Staging-capable | YES (`render.yaml`, compose) |
| Production-capable | PARTIAL — auth-off risk, Alembic head sparse, dual-app confusion |
| SaaS-capable | NO |

## Website deployment readiness

**STAGING_READY** — Pages staging identity exists; custom domain / SEO origin still operational debt (FDR-N05 / N0 docs).

## Explicit answers

| Question | Answer |
|----------|--------|
| Where is the public website hosted? | Cloudflare Pages (static) |
| Where is Founder OS app expected to run? | uvicorn process (local/Docker/Render) |
| Can the app be deployed publicly? | Technically yes; product-ready only with auth hardening |
| Does Cloudflare host the application? | NO |
