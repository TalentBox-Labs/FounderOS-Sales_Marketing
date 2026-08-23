# S1 — Operator Readiness Guide

**Sprint:** S1  
**Agent:** BEACON

---

## Primary question

**What prevents this page from being SEO-ready?**

Answer order:

1. **DOMAIN BLOCKERS** — cannot activate production SEO (domain / indexing gates)
2. **ERRORS** — technical blockers (missing title, bad slug, invalid JSON-LD, …)
3. **WARNINGS** — should fix before go-live
4. **INFORMATION** — advisory (no H2, no robots meta, no internal links)

A high score **never** overrides DOMAIN BLOCKERS.

---

## How to read a report

```text
status: DOMAIN_BLOCKED | ERROR | WARNING | PASS
score: 0–100 (transparent penalties)
domain_blockers: [...]
errors: [...]
warnings: [...]
info: [...]
checks: { id → detail + recommendation }
```

### Operator UI

- `/seo` — site list (status, score, blocker/error/warning counts)
- `/seo/{slug}` — “What prevents SEO-ready?” + actionable recommendations

### API

- `GET /api/v1/seo/readiness`
- `GET /api/v1/seo/readiness/{slug}`

Both are **read-only**. No Fix / Publish / Index / Submit / AI rewrite controls.

---

## Typical S1 outcomes (current governance)

| Situation | Expected status |
|-----------|-----------------|
| Technically healthy page + placeholder origin | DOMAIN_BLOCKED |
| Page with workcrew.ai canonical | DOMAIN_BLOCKED (+ errors if other issues) |
| Missing title | ERROR (and likely DOMAIN_BLOCKED until domain ratified) |
| Domain ratified + healthy page | PASS (future — not available until FDR-N05) |

---

## What S1 does NOT do

- Generate replacement marketing copy
- Optimize keyword strategy
- Call LLMs or external APIs
- Auto-edit content
- Auto-publish or auto-index

---

## Recommended operator workflow

1. Publish / render via Website Engine (existing flow).
2. Open `/seo` or call readiness API.
3. Fix ERRORs in content/source via Editorial / Content Studio (human).
4. Treat DOMAIN BLOCKERS as governance — wait for Founder domain ratification.
5. Do not submit sitemaps or configure Search Console in S1.
