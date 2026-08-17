# Founder OS Architecture v2.2 — Diagrams

**Status:** FROZEN (companion to Architecture_v2.2.md)  
**Sprint:** A1 (updated from G1 v2.1 diagrams)  
**Date:** 2026-08-10  
**Parent:** [Architecture_v2.2.md](Architecture_v2.2.md)

Governance only. No runtime or code changes.

---

## 1. System map

```text
┌──────────────────────────────────────────────────────────────────────────┐
│                              FOUNDER OS                                  │
├───────────────┬───────────────┬───────────────┬──────────────────────────┤
│ Executive OS  │   Sales OS    │  Revenue OS   │      Marketing OS        │
├───────────────┴───────────────┴───────────────┤  Content Studio          │
│         Customer Success OS                   │  Editorial Engine        │
│         Operations OS                         │  Publishing Engine       │
│         Knowledge OS                          │  Website Engine          │
│                                               │  Campaign / SEO/GEO/AEO  │
│                                               │  Social / Email / Brand  │
│                                               │  Video* Newsletter*      │
│                                               │  Community* (*FUTURE)    │
└───────────────────────────────────────────────┴──────────────────────────┘
                │ consumes                         │ consumes
                ▼                                  ▼
┌─────────────────────────────┐  ┌─────────────────────────────┐
│        AI Platform          │  │   Automation Platform       │
│ LLM · Prompts · Memory      │  │ Scheduler · Celery · n8n    │
│ Embeddings · RAG · Agents   │  │ Queues · Events · Webhooks  │
│ Evaluation                  │  │ Workers · Retries           │
└─────────────────────────────┘  └─────────────────────────────┘
                │                                  │
                └──────────────┬───────────────────┘
                               ▼
                 ┌─────────────────────────────┐
                 │      Shared Platform        │
                 │ Auth · RBAC · Audit · Secrets│
                 │ Config · Storage · Notify   │
                 │ Observability · Search      │
                 │ API Gateway                 │
                 └─────────────────────────────┘
```

---

## 2. Marketing OS hierarchy (v2.2)

```text
Marketing OS
├── SHIPPED / CORE
│   ├── Content Studio
│   ├── Editorial Engine
│   ├── Publishing Engine
│   └── Website Engine
├── DESTINATION (partial or not started)
│   ├── Campaign Engine
│   ├── SEO / GEO / AEO Engines
│   ├── Social Engine
│   ├── Email Engine
│   └── Brand Engine
└── FUTURE (named only in v2.2)
    ├── Video Engine
    ├── Newsletter Engine
    └── Community Engine
```

---

## 3. Publish path (destination)

```text
Editorial (human) → Publishing (orchestrate) → channel engines
                                              Website | Social | Email | Video* | Newsletter*
```

---

## 4. Agent → Approval → Automation flow

```text
  Agent (AI Platform runtime)
           |
           v
     Recommendation
           |
           v
  Human Approval (when required)
           |
           v
  Automation Platform (execute only)
           |
           v
       Execution
           |
           v
  Audit (Shared Platform)
```

---

## 5. Allowed dependency arrows

```text
OS --------------> AI Platform
OS --------------> Automation Platform
OS --------------> Shared Platform

Publishing Engine --> Website / Social / Email / (future Video / Newsletter)

FORBIDDEN:
  Platform --business decision--> OS
  Publishing Engine owns HTML/sitemap
  Future engines implemented silently without ADR
```
