# MDG0 — Audience Surface Audit

**Sprint:** MDG0  
**Date:** 2026-08-13  
**Mode:** AUDIT ONLY  
**Feature Code Changes:** 0

## Question

What audience-facing surfaces exist, and can any of them create demand?

## Inventory

| # | Surface | Classification | Evidence |
|---|---------|----------------|----------|
| 1 | Public website / Website Engine / static output | **LIVE** (reach) / **PARTIAL** (demand-ready) | `src/tools/website_engine/`, `output/website/`, Cloudflare Pages via `src/tools/website_deployment/` |
| 2 | Content Studio | **LIVE** | `runner_api_routers/content_studio.py`, `/content-studio*` |
| 3 | Editorial Engine | **LIVE** | `runner_api_routers/editorial.py`, `/editorial*` |
| 4 | Publishing Engine | **LIVE** (orchestration) / **PARTIAL** (channel delivery) | `runner_api_routers/publishing.py`; website adapter partially wired; social adapters `NOT_IMPLEMENTED` |
| 5 | SEO Readiness | **LIVE** (engine+UI) / **BLOCKED** (prod indexing) | `runner_api_routers/seo.py`, `/seo`; FDR-N05 domain pending |
| 6 | Technical SEO | **LIVE** (engine+UI) / **BLOCKED** (prod activation) | `/seo/technical`; same domain gate |
| 7 | RSS / feeds | **LIVE** | `src/tools/website_engine/feeds.py`, `output/website/rss.xml` |
| 8 | Social infrastructure | **DORMANT** / **BLOCKED** | Publishing adapters `NOT_IMPLEMENTED`; S0 blockers FD-01 / ES-01..03 |
| 9 | Interactive CTAs | **MISSING** | Content plans mention CTA; rendered static HTML has no CTA UI / form |
| 10 | Contact / signup / newsletter / demo forms | **MISSING** | No public `<form>` in `output/website/`; CP4 confirms Turnstile absent |
| 11 | Landing / campaign pages | **MISSING** | No campaign package; static v1 lacks root marketing landing demand path |
| 12 | Inbound APIs / webhooks / tracking | **PARTIAL** | MC04 handoff API (human); n8n outreach webhooks (not audience→demand); no form handler / UTM ingest |

## Counts

| Class | Count |
|-------|------:|
| LIVE (ops/reach) | 5 |
| PARTIAL | 4 |
| DORMANT / BLOCKED | 1 |
| MISSING | 3 |
| **Surfaces audited** | **12** |

## Verdict

Audience **reach** exists. Audience **conversion** does not. No live surface turns a visitor into a demand record.
