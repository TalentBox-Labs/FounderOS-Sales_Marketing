# Founder OS Architecture v2.0

**Status:** SUPERSEDED (destination) by **Architecture v2.1** — see [Architecture_v2.1.md](Architecture_v2.1.md)  
**Historical freeze:** G0 — 2026-08-09 (ADR-001)  
**Canonical repository:** `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`

> **Current canonical destination:** [Architecture_v2.1.md](Architecture_v2.1.md) (Website Engine added; Publishing Engine narrowed).  
> This v2.0 document is retained as the historical freeze record. Do not use v2.0 as the active destination map.

**Nature of this document:** Destination architecture (governance) as of G0.  
**Does not change:** current implementation, APIs, database, runtime, or business logic.

Supersedes prior planning narratives for long-term structure (as of v2.0).  
Does **not** invalidate frozen baselines (Architecture Baseline v1.x, Runtime Baseline, Content Studio, Editorial Readiness/Approval Phase 1, Toolchain Baseline).

Related:

- [Architecture_v2.1.md](Architecture_v2.1.md) ← **current**
- [Architecture_v2_Diagram.md](Architecture_v2_Diagram.md)
- [Architecture_Principles.md](Architecture_Principles.md)
- [Platform_vs_OS_Boundaries.md](Platform_vs_OS_Boundaries.md)
- [Future_Module_Roadmap.md](Future_Module_Roadmap.md)
- [Migration_Target_Architecture.md](Migration_Target_Architecture.md)
- [Marketing_OS.md](Marketing_OS.md)
- [Architecture_ADR_001.md](Architecture_ADR_001.md)
- [Architecture_ADR_002.md](Architecture_ADR_002.md)

---

## 1. Purpose

Define the canonical long-term architecture of **Founder OS** so that every OS module and Platform has a clear owner, boundary, and dependency direction.

This is the **destination map**. Current code may partially implement, approximate, or co-locate concerns. Migration moves toward this map without rewriting history.

---

## 2. Canonical structure

```
Founder OS
├── Executive OS
├── Sales OS
├── Revenue OS
├── Marketing OS
│   ├── Content Studio
│   ├── Editorial Engine
│   ├── Publishing Engine
│   ├── Campaign Engine
│   ├── SEO Engine
│   ├── GEO Engine
│   ├── AEO Engine
│   ├── Social Engine
│   ├── Email Engine
│   └── Brand Engine
├── Customer Success OS
├── Operations OS
├── Knowledge OS
├── AI Platform
├── Automation Platform
└── Shared Platform
```

---

## 3. Layer definitions

### 3.1 OS modules

OS modules own **business decisions** and domain workflows for their vertical.

| OS | Owns (destination) |
|----|--------------------|
| **Executive OS** | Founder/executive dashboards, cross-OS KPIs, decision summaries |
| **Sales OS** | Prospecting, outreach sequences, SDR workflows, sales pipeline ops |
| **Revenue OS** | CRM entities, deals, forecasting, revenue automations, GTM orchestration (revenue side) |
| **Marketing OS** | Content lifecycle, editorial, publishing, campaigns, SEO/GEO/AEO, brand, social, email |
| **Customer Success OS** | Accounts, health, renewals, CS playbooks |
| **Operations OS** | Internal ops workflows, runbooks, operational coordination |
| **Knowledge OS** | Knowledge base corpus, retrieval products, internal knowledge workflows |

### 3.2 Platforms

Platforms own **infrastructure**. They do not own product/business decisions.

| Platform | Owns (destination) |
|----------|--------------------|
| **AI Platform** | LLM routing, prompt registry, memory, embeddings, RAG infra, model providers, agent runtime, evaluation |
| **Automation Platform** | Scheduler, Celery, n8n, queues, events, workers, retries, webhooks — **no business logic** |
| **Shared Platform** | AuthN/AuthZ, RBAC, audit, secrets, config, storage, notifications, observability, search infra, API gateway |

---

## 4. Marketing OS (detail)

Marketing OS owns marketing business decisions and the content → publish → amplify lifecycle.

| Engine | Destination responsibility |
|--------|----------------------------|
| **Content Studio** | Inventory, status views, kanban, artifact presence (operator surface over content SoT) |
| **Editorial Engine** | Readiness evidence, human editorial approval, phase-scoped promote attestation |
| **Publishing Engine** | Production publish / go-live after separate human gates |
| **Campaign Engine** | Campaign definition, launch gates, campaign orchestration decisions |
| **SEO Engine** | SEO planning, keyword/rank business logic |
| **GEO Engine** | Generative Engine Optimization strategies and content fitness for GEO |
| **AEO Engine** | Answer Engine Optimization strategies and structured answer fitness |
| **Social Engine** | Social channel copy/distribution decisions |
| **Email Engine** | Email copy/distribution decisions |
| **Brand Engine** | Brand voice, brand policy, brand-constrained review |

Marketing OS **consumes** AI Platform and Automation Platform. It does not own LLM infra, Celery, or auth.

---

## 5. AI Platform

Owns AI **infrastructure only**.

| Capability | Notes |
|------------|--------|
| LLM routing | Provider/model selection, failover |
| Prompt registry | Versioned prompts; no OS-specific business ownership of outcomes |
| Memory | Agent/session memory stores |
| Embeddings | Embedding pipelines and stores |
| RAG | Retrieval infrastructure (indexes, chunking infra) |
| Model providers | OpenAI / Gemini / Ollama / etc. adapters |
| Agent runtime | Crew/agent execution substrate |
| Evaluation | Eval harnesses, quality scoring infra |

**Consumers:** Marketing OS, Sales OS, Revenue OS, Knowledge OS, others as needed.

Agents **recommend**. They do not approve mandatory human gates.

---

## 6. Automation Platform

Owns **execution** machinery.

| Capability | Notes |
|------------|--------|
| Scheduler | Cron / beat schedules |
| Celery | Task workers |
| n8n | External workflow bridge |
| Queues / Events | Job and event transport |
| Workers / Retries | Execution reliability |
| Webhooks | Inbound/outbound delivery hooks |

**Law:** No business logic inside Automation Platform. OS modules decide *what*; Automation executes *how/when* after approval.

---

## 7. Shared Platform

Owns reusable cross-cutting infrastructure:

Authentication · Authorization · RBAC · Audit · Secrets · Configuration · Storage · Notifications · Observability · Search (infra) · API Gateway

OS modules must not re-implement these as parallel platforms.

---

## 8. Architectural law

1. **Business logic belongs to OS modules.**
2. **Infrastructure belongs to Platforms.**
3. **OS modules may never own infrastructure.**
4. **Platforms may never own business decisions.**

---

## 9. Agent governance (canonical flow)

```
Agent
  ↓
Recommendation
  ↓
Human Approval (when required)
  ↓
Automation Platform
  ↓
Execution
  ↓
Audit
```

Rules:

- Agents recommend.
- Humans approve where required.
- Automation executes.
- All execution is audited.

---

## 10. Mandatory human gates

These decisions require a human before execution proceeds:

| Gate | Owning OS (destination) |
|------|-------------------------|
| Editorial approval | Marketing OS / Editorial Engine |
| Campaign launch | Marketing OS / Campaign Engine |
| Production publishing | Marketing OS / Publishing Engine |
| Brand policy changes | Marketing OS / Brand Engine |
| Revenue-impacting automations | Revenue OS (+ Shared Platform audit) |
| Customer-facing AI policy | Shared Platform + relevant OS (policy owners) |

Editorial approval **does not** authorize publishing (FDR-003 / E7). Publishing remains a separate gate.

---

## 11. Dependency direction (destination)

```
OS modules  →  consume  →  AI Platform
OS modules  →  consume  →  Automation Platform
OS modules  →  consume  →  Shared Platform

Platforms do not call OS modules for business decisions.
Platforms may emit events; OS modules interpret business meaning.
```

Forbidden destination patterns:

- Marketing OS owning Celery app configuration as product logic
- AI Platform deciding campaign launch or editorial approve
- Automation Platform encoding SEO strategy or brand policy
- Revenue OS `/approvals` conflated with Editorial Approval

---

## 12. Relationship to current implementation

| Statement | Status |
|-----------|--------|
| Current implementation remains valid | **YES** |
| This document changes runtime | **NO** |
| This document changes APIs | **NO** |
| This document changes database | **NO** |
| This document changes business logic | **NO** |
| Sprint baselines remain compatible | **YES** (see ADR-001) |

Known co-location in today’s codebase (not rewritten by G0):

- Combined `runner_api` surface hosts multiple OS concerns
- CrewAI runtime lives under `src` while Revenue AI services exist separately
- Celery/Redis used by Revenue/Automation paths
- Editorial Approval Phase 1 and Content Studio already align directionally with Marketing OS engines

G0 freezes the **target map** only. Migration is governed separately (see Migration_Target_Architecture.md).

---

## 13. Freeze declaration

**FOUNDATION ARCHITECTURE v2.0 FROZEN**

Any future sprint that relocates ownership, introduces a new OS/Platform, or moves a mandatory human gate must amend Architecture v2.0 via ADR and governance approval.

---

## 14. Impact verification (G0)

| Dimension | Impact |
|-----------|--------|
| Architecture impact (implementation) | **NONE** |
| Runtime impact | **NONE** |
| API impact | **NONE** |
| Database impact | **NONE** |
| Git operations (this sprint) | **NONE** |
| Code changes (this sprint) | **NONE** |
