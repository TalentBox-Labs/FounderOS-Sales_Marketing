# Marketing OS — Module Documentation (Architecture v2.1)

**Status:** SUPERSEDED (destination) by [Marketing_OS_v2.2.md](Marketing_OS_v2.2.md)  
**Historical freeze:** G1 — 2026-08-09  
**Parent:** [Architecture_v2.1.md](Architecture_v2.1.md)  
**ADR:** [Architecture_ADR_002.md](Architecture_ADR_002.md)

> **Current Marketing OS docs:** [Marketing_OS_v2.2.md](Marketing_OS_v2.2.md) under Architecture v2.2.

Governance only. No feature implementation in G1.

---

## 1. Purpose

Marketing OS owns business decisions for marketing: content lifecycle, editorial, publication orchestration, website, campaigns, SEO/GEO/AEO, brand, social, and email.

It **consumes** AI Platform, Automation Platform, and Shared Platform.  
It does **not** own LLM infra, Celery, or auth.

---

## 2. Module hierarchy

```
Marketing OS
├── Content Studio
├── Editorial Engine
├── Publishing Engine
├── Website Engine          ← v2.1
├── Campaign Engine
├── SEO Engine
├── GEO Engine
├── AEO Engine
├── Social Engine
├── Email Engine
└── Brand Engine
```

---

## 3. Responsibility matrix

| Engine | Owns | Does not own |
|--------|------|--------------|
| **Content Studio** | Content planning, editing, organization | Publish auth, website render, campaign launch |
| **Editorial Engine** | Review workflow, approvals, editorial governance, audit trail | Production publish, website CMS, social APIs |
| **Publishing Engine** | Publication orchestration; consume approved artifacts; destination channels; publishing jobs; publish queue | Website implementation, rendering, SEO ownership, social APIs |
| **Website Engine** | Canonical Founder website: MD→HTML, slugs, canonical URLs, metadata, OpenGraph, Schema.org, RSS, sitemap, static assets, website API, future WordPress/Ghost, search index hooks, cache invalidation, deploy hooks; **website publishing only** | Campaign logic, social publishing |
| **Campaign Engine** | Scheduling, campaign orchestration, sequences, publishing windows, multi-channel coordination | Website rendering, editorial approve |
| **SEO Engine** | SEO scoring, keywords, internal linking, metadata optimization, search readiness | Website deploy, social adapters |
| **GEO Engine** | Generative Engine Optimization, LLM discoverability, citation optimization, knowledge graph optimization | Embedding infra (AI Platform) |
| **AEO Engine** | Answer Engine Optimization, structured answers, FAQ generation, snippet optimization | Publish queue ownership |
| **Social Engine** | LinkedIn, X, Instagram, Facebook, future platforms; channel-specific publishing adapters | Website publishing, email subscriber DB |
| **Email Engine** | Newsletter generation, email campaigns, email publishing, subscriber workflows | Website sitemap, social APIs |
| **Brand Engine** | Brand compliance, voice/style/terminology validation, brand governance | AuthN, Celery |

---

## 4. Destination publish flow

```
Content Studio  →  Editorial Engine (human gate)
                         ↓
                 Publishing Engine (orchestrate)
                         ↓
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
   Website Engine   Social Engine   Email Engine
   (site only)      (adapters)      (email)
          ▲
          │ advice / readiness (not ownership of site)
   SEO / GEO / AEO / Brand Engines
```

Campaign Engine may set windows and multi-channel sequences; it does not render the website.

---

## 5. Human gates (Marketing OS)

| Gate | Engine |
|------|--------|
| Editorial approval | Editorial Engine |
| Production publishing | Publishing Engine (orchestration decision) + channel engines execute |
| Campaign launch | Campaign Engine |
| Brand policy changes | Brand Engine |

Editorial approval does **not** authorize publishing.

---

## 6. Shipped vs destination

| Engine | Shipped (approx.) | Destination note |
|--------|-------------------|------------------|
| Content Studio | Read API + UI + kanban frozen | Planning/editing/organization surfaces expand additively |
| Editorial Engine | Readiness + Approval Phase 1 | Governance continues; ≠ publish |
| Publishing Engine | **Not started** | M1 Phase 1 = orchestration only |
| Website Engine | **Not started** (G1 docs only) | Zero code in G1 |
| Others | Partial / nascent | Per Future_Module_Roadmap |

---

## 7. Compatibility

- Architecture v2.0 Marketing OS list remains historically valid; v2.1 is current.
- No prior Marketing sprint invalidated.
- Ready for **M1 — Publishing Engine Phase 1** without Website Engine code.
