# S2 — Technical SEO Operator Guide

**Sprint:** S2  
**Agent:** BEACON

---

## Question answered

**Is the generated Founder OS website technically healthy for crawling, indexing, and search interpretation once a production domain is ratified?**

---

## How to read severity

| Operator term | Implementation |
|---------------|----------------|
| DOMAIN BLOCKER | `DOMAIN_BLOCKED` |
| CRITICAL TECHNICAL ISSUE | `CRITICAL` |
| ERROR | `ERROR` |
| WARNING | `WARNING` |
| INFORMATION | `INFO` |

Numeric technical score is optional context and **never** overrides blockers.

---

## Surfaces

| Surface | Use |
|---------|-----|
| `/seo` | S1 readiness (frozen) |
| `/seo/technical` | S2 technical summary |
| `GET /api/v1/seo/technical` | Machine-readable site report |

---

## Typical current state (pre-domain)

- Many **DOMAIN BLOCKERS** while origin unratified and historical `workcrew.ai` URLs remain in artifacts  
- Website Engine **WARNING**: no page `noindex` on deprecated/infra hosts → accidental index risk  
- No Fix / Rewrite / Publish / Index / Submit / Crawl Internet actions  

---

## Non-goals

- Keyword research  
- Copy generation / LLM recommendations  
- Auto-repair of Website Engine or content  
- GEO / AEO implementation
