# Marketing OS — Module Documentation (Architecture v2.2)

**Status:** FROZEN (governance)  
**Sprint:** A1  
**Date:** 2026-08-10  
**Parent:** [Architecture_v2.2.md](Architecture_v2.2.md)  
**ADR:** [Architecture_ADR_003.md](Architecture_ADR_003.md)

Governance only. No feature implementation in A1.

---

## 1. Purpose

Marketing OS owns business decisions for marketing: content lifecycle, editorial, publication orchestration, website, campaigns, SEO/GEO/AEO, brand, social, email, and (future) video, newsletter specialization, and community.

Consumes: AI Platform, Automation Platform, Shared Platform.  
Does **not** own: LLM infra, Celery, auth stacks.

---

## 2. Module hierarchy

```
Marketing OS
├── Content Studio
├── Editorial Engine
├── Publishing Engine
├── Website Engine
├── Campaign Engine
├── SEO Engine
├── GEO Engine
├── AEO Engine
├── Social Engine
├── Email Engine
├── Brand Engine
├── Video Engine              ← FUTURE
├── Newsletter Engine         ← FUTURE
└── Community Engine          ← FUTURE
```

---

## 3. Responsibility matrix (summary)

| Engine | Owns | Does not own |
|--------|------|--------------|
| Content Studio | Planning, editing, organization | Publish auth, website render |
| Editorial Engine | Review, approvals, governance, audit | Production publish, website CMS |
| Publishing Engine | Orchestration: jobs, queue, channels | Website render, SEO scoring, social APIs |
| Website Engine | Canonical site render/publish/static/deploy hooks | Campaign, social |
| Campaign Engine | Sequences, windows, multi-channel coordination | Website rendering |
| SEO Engine | Scoring, keywords, linking, search readiness | Site deploy |
| GEO Engine | LLM discoverability / citation / KG optimization | Embedding infra |
| AEO Engine | Structured answers, FAQ, snippets | Publish queue |
| Social Engine | Social channel adapters | Website publishing |
| Email Engine | Email campaigns / publishing / subscribers | Website sitemap |
| Brand Engine | Brand compliance & governance | AuthN |
| Video Engine | Video content lifecycle (future) | Social live streaming platforms as SoT |
| Newsletter Engine | Newsletter product lifecycle (future) | Generic transactional email infra |
| Community Engine | Community surfaces & programs (future) | CRM deal ownership |

---

## 4. Engine specifications

### 4.1 Content Studio

| Field | Definition |
|-------|------------|
| **Mission** | Operator surface for content planning, editing, and organization over Founder content SoT. |
| **Responsibilities** | Inventory, status views, kanban, artifact presence, navigation into editorial/publish contexts. |
| **Inputs** | `tracker.csv`, `input/{week}/` artifacts, Content Studio APIs. |
| **Outputs** | Read models, UI views; does not mutate publish authorization. |
| **Dependencies** | Shared Platform (HTTP shell); Editorial/Publishing for downstream gates. |
| **Current status** | **SHIPPED** — read API + list/detail + kanban baselines frozen. |
| **Future status** | Additive planning/editing; calendar blocked until date SoT ADR. |

### 4.2 Editorial Engine

| Field | Definition |
|-------|------------|
| **Mission** | Human editorial governance: readiness evidence, approvals, audit. |
| **Responsibilities** | Review workflow, approve/reject/request-changes, phase-scoped promote attestation, audit trail. |
| **Inputs** | Content bundles, QA reports, staging, human approver. |
| **Outputs** | Decision audit (`output/editorial_decisions/`), promote into `input/{week}/` on approve. |
| **Dependencies** | Content Studio evidence; AI Platform for recommend-only crews; Shared audit patterns. |
| **Current status** | **SHIPPED** — readiness + Approval Phase 1 (E7). |
| **Future status** | Expand states/gates; never authorizes publish (FDR-003). |

### 4.3 Publishing Engine

| Field | Definition |
|-------|------------|
| **Mission** | Publication orchestration only. |
| **Responsibilities** | Read approved bundles; validate publish readiness; jobs; queue; channel selection; state machine; audit; manual publish. |
| **Inputs** | Editorial approval evidence; channel id; human requester. |
| **Outputs** | Jobs under `output/publishing/`; channel adapter results (PLACEHOLDER / NOT_IMPLEMENTED / future engine calls). |
| **Dependencies** | Editorial Engine; channel engines (Website/Social/Email); Automation only for future job transport — not in Phase 1. |
| **Current status** | **SHIPPED** — Phase 1 + baseline freeze (M1 / M1.5). |
| **Future status** | Wire website channel to Website Engine; keep orchestration-only. |

### 4.4 Website Engine

| Field | Definition |
|-------|------------|
| **Mission** | Own the canonical Founder website. |
| **Responsibilities** | Content model, slug/URL, metadata, render, sitemap/RSS, provider adapters (static shipped), future CMS/deploy hooks. |
| **Inputs** | Approved filesystem bundles (`input/{week}/05_Final.md` etc.). |
| **Outputs** | `output/website/` artifacts; provider results compatible with Publishing channel contract. |
| **Dependencies** | Publishing for orchestration jobs (optional wire); Shared/Automation for future deploy transport. |
| **Current status** | **SHIPPED** — Core + Static Provider (M2–M3.5 baselines). |
| **Future status** | M4 deployment-mode decision; WordPress/Ghost adapters later. |

### 4.5 Campaign Engine

| Field | Definition |
|-------|------------|
| **Mission** | Campaign orchestration across channels and time windows. |
| **Responsibilities** | Scheduling intent, sequences, publishing windows, multi-channel coordination, launch human gate. |
| **Inputs** | Campaign definitions; channel engine readiness; brand constraints. |
| **Outputs** | Launch decisions; coordinated publish intents (not channel rendering). |
| **Dependencies** | Publishing Engine; Social/Email/Website/Video (future); Automation for schedules. |
| **Current status** | **NOT STARTED**. |
| **Future status** | Destination engine; implement after Publishing/Website stable. |

### 4.6 SEO Engine

| Field | Definition |
|-------|------------|
| **Mission** | Search Engine Optimization strategy and readiness for Founder content. |
| **Responsibilities** | SEO scoring, keywords, internal linking advice, metadata optimization guidance, search readiness. |
| **Inputs** | Content drafts/finals; keyword data; rank signals (when available). |
| **Outputs** | SEO plans/scores/recommendations (not site deploy). |
| **Dependencies** | Content Studio / Editorial artifacts; AI Platform for assistive scoring; Website Engine consumes metadata emission separately. |
| **Current status** | **PARTIAL** — SEO API/tools exist; not a formal engine package. |
| **Future status** | Formalize under Marketing OS without owning Website deploy. |

### 4.7 GEO Engine

| Field | Definition |
|-------|------------|
| **Mission** | Generative Engine Optimization — LLM discoverability and citation fitness. |
| **Responsibilities** | GEO strategies, citation optimization, knowledge-graph optimization guidance. |
| **Inputs** | Content bundles; entity/knowledge signals. |
| **Outputs** | GEO recommendations / fitness reports. |
| **Dependencies** | AI Platform (embeddings/RAG infra); Knowledge OS for corpus where relevant. |
| **Current status** | **NOT STARTED** as named engine. |
| **Future status** | Destination engine. |

### 4.8 AEO Engine

| Field | Definition |
|-------|------------|
| **Mission** | Answer Engine Optimization — structured answers and snippet fitness. |
| **Responsibilities** | Structured answers, FAQ generation, snippet optimization. |
| **Inputs** | Content bundles; Q&A intents. |
| **Outputs** | FAQ/structured answer artifacts; recommendations. |
| **Dependencies** | AI Platform; Editorial for quality gates. |
| **Current status** | **NOT STARTED** as named engine. |
| **Future status** | Destination engine. |

### 4.9 Social Engine

| Field | Definition |
|-------|------------|
| **Mission** | Social channel publishing adapters. |
| **Responsibilities** | LinkedIn, X, Instagram, Facebook, future platforms; channel-specific publish adapters. |
| **Inputs** | Publishing jobs for social channels; approved copy artifacts. |
| **Outputs** | Channel publish results; no website HTML ownership. |
| **Dependencies** | Publishing Engine orchestration; Automation for delivery jobs; Shared secrets. |
| **Current status** | **NOT STARTED** — Publishing stubs return `NOT_IMPLEMENTED`. |
| **Future status** | Destination engine after Website/Publishing baselines. |

### 4.10 Email Engine

| Field | Definition |
|-------|------------|
| **Mission** | Email channel publishing and subscriber workflows. |
| **Responsibilities** | Email campaigns, email publishing, subscriber workflows; distribution email copy. |
| **Inputs** | Publishing jobs (`newsletter` channel today); email copy artifacts. |
| **Outputs** | Email send/orchestration results (future). |
| **Dependencies** | Publishing Engine; Automation; Shared secrets. |
| **Current status** | **PARTIAL** / nascent — artifacts + channel stub; not formal engine. |
| **Future status** | Formalize; coordinate with Newsletter Engine (future) without conflating product newsletter ownership prematurely. |

### 4.11 Brand Engine

| Field | Definition |
|-------|------------|
| **Mission** | Brand compliance and voice governance. |
| **Responsibilities** | Brand compliance, voice/style/terminology validation, brand policy human gate. |
| **Inputs** | Content drafts; brand policy corpus. |
| **Outputs** | Pass/fail brand reports; policy change audit. |
| **Dependencies** | Editorial/Content Studio; AI Platform for assistive checks only. |
| **Current status** | **PARTIAL** — implicit in validators/crews. |
| **Future status** | Explicit Brand Engine package + human gate. |

### 4.12 Video Engine (FUTURE)

| Field | Definition |
|-------|------------|
| **Mission** | Own video content lifecycle for Marketing OS (script → asset → publish intent). |
| **Responsibilities** | Video planning, scripts, asset inventory, video-specific metadata; publish via Publishing orchestration to video-capable channels. |
| **Inputs** | Briefs, scripts, media assets (future SoT). |
| **Outputs** | Video packages; readiness for campaign/social/website embeds. |
| **Dependencies** | Content Studio; Editorial; Publishing; Social/Website for distribution; AI Platform for assistive generation. |
| **Current status** | **NOT IMPLEMENTED** — named in Architecture v2.2 only. |
| **Future status** | Destination engine; no A1 code. |

### 4.13 Newsletter Engine (FUTURE)

| Field | Definition |
|-------|------------|
| **Mission** | Own the newsletter product lifecycle (editions, cadence, list segments as marketing product). |
| **Responsibilities** | Newsletter edition planning, composition, edition approval coordination, handoff to Email Engine / Publishing for delivery. |
| **Inputs** | Editorial content; subscriber segment definitions (future). |
| **Outputs** | Newsletter editions ready for email channel publish. |
| **Dependencies** | Editorial; Email Engine; Publishing; Brand; Campaign for cadence. |
| **Current status** | **NOT IMPLEMENTED** — named in Architecture v2.2 only. |
| **Future status** | Destination engine; may specialize vs Email Engine via later ADR if needed. |

### 4.14 Community Engine (FUTURE)

| Field | Definition |
|-------|------------|
| **Mission** | Own community programs and community-facing marketing surfaces. |
| **Responsibilities** | Community content programs, engagement playbooks, community channel coordination (not CRM ownership). |
| **Inputs** | Brand guidelines; campaign intents; community content. |
| **Outputs** | Community program artifacts; publish intents via Publishing/Social as applicable. |
| **Dependencies** | Brand; Campaign; Social; Knowledge OS (optional); Shared Platform. |
| **Current status** | **NOT IMPLEMENTED** — named in Architecture v2.2 only. |
| **Future status** | Destination engine; no A1 code. |

---

## 5. Destination publish flow

```
Content Studio  →  Editorial Engine (human gate)
                         ↓
                 Publishing Engine (orchestrate)
                         ↓
     ┌───────────┬───────┴───────┬───────────┬──────────┐
     ▼           ▼               ▼           ▼          ▼
 Website     Social          Email      Video*    Newsletter*
 Engine      Engine          Engine     Engine*   Engine*
     ▲
 SEO / GEO / AEO / Brand (+ Campaign windows)
```

\* Future engines — not implemented in A1.

---

## 6. Human gates (Marketing OS)

| Gate | Engine |
|------|--------|
| Editorial approval | Editorial Engine |
| Production publishing | Publishing Engine + channel engines |
| Campaign launch | Campaign Engine |
| Brand policy changes | Brand Engine |

Editorial approval does **not** authorize publishing.

---

## 7. Compatibility

- Architecture v2.1 Marketing OS docs remain historically valid; **v2.2 is current**.
- No prior Marketing sprint invalidated.
- Ready for **G2 — Platform Agent Registry** (platform naming; not Marketing feature work).
