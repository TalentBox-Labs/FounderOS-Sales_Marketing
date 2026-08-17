# Founder OS Architecture v2.1

**Status:** SUPERSEDED (destination) by **Architecture v2.2** — see [Architecture_v2.2.md](Architecture_v2.2.md)  
**Historical freeze:** G1 — 2026-08-09 (ADR-002)  
**Canonical repository:** `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`  
**Supersedes (destination):** Architecture v2.0 ([Architecture_v2.md](Architecture_v2.md))  
**ADR:** [Architecture_ADR_002.md](Architecture_ADR_002.md)

> **Current canonical destination:** [Architecture_v2.2.md](Architecture_v2.2.md) (future Marketing OS engines named; shipped status reflected).  
> This v2.1 document is retained as the historical freeze record.

**Nature:** Destination architecture (governance only) as of G1.  
**Does not change:** current implementation, APIs, database, runtime, or business logic.

v2.1 refinement: **Website Engine** added under Marketing OS.  
Publishing Engine owns **publication orchestration only**; Website Engine owns **canonical website rendering and website publishing**.

Related:

- [Architecture_v2.2.md](Architecture_v2.2.md) ← **current**
- [Architecture_v2_Diagram.md](Architecture_v2_Diagram.md)
- [Architecture_Principles.md](Architecture_Principles.md)
- [Platform_vs_OS_Boundaries.md](Platform_vs_OS_Boundaries.md)
- [Future_Module_Roadmap.md](Future_Module_Roadmap.md)
- [Migration_Target_Architecture.md](Migration_Target_Architecture.md)
- [Marketing_OS_v2.2.md](Marketing_OS_v2.2.md)
- [Marketing_OS.md](Marketing_OS.md)
- [Architecture_ADR_001.md](Architecture_ADR_001.md) (v2.0 freeze)
- [Architecture_ADR_002.md](Architecture_ADR_002.md) (v2.1 Website Engine)
- [Architecture_ADR_003.md](Architecture_ADR_003.md) (v2.2)

---

## 1. Purpose

Canonical long-term architecture of **Founder OS**, refined from v2.0 to separate:

| Concern | Owner |
|---------|-------|
| Publication orchestration (channels, jobs, queue) | **Publishing Engine** |
| Canonical website (render, URLs, metadata, site deploy) | **Website Engine** |

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
│   ├── Website Engine          ← NEW in v2.1
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

## 3. Marketing OS — engine responsibilities

### Content Studio

- Content planning
- Content editing
- Content organization

Does **not** authorize publishing or own website rendering.

### Editorial Engine

- Review workflow
- Approvals
- Editorial governance
- Audit trail

Does **not** authorize production publishing (FDR-003). Does **not** own website implementation.

### Publishing Engine

Owns **publication orchestration only**.

- Consumes approved editorial artifacts
- Determines destination channels
- Creates publishing jobs
- Creates publish queue

Does **NOT**:

- Know website implementation
- Own rendering
- Own SEO
- Own social APIs

### Website Engine (NEW)

Owns the **canonical Founder website**.

Responsible for:

- Markdown rendering
- HTML generation
- Slug generation
- Canonical URLs
- Metadata
- OpenGraph
- Schema.org
- RSS
- Sitemap
- Static assets
- Website API integration
- WordPress integration (future)
- Ghost integration (future)
- Search indexing hooks
- Website cache invalidation
- Website deployment hooks

Owns **website publishing only**.

Does **NOT** own:

- Campaign logic
- Social publishing

### Campaign Engine

- Scheduling
- Campaign orchestration
- Sequences
- Publishing windows
- Multi-channel coordination

### SEO Engine

- SEO scoring
- Keywords
- Internal linking
- Metadata optimization
- Search readiness

### GEO Engine

- Generative Engine Optimization
- LLM discoverability
- Citation optimization
- Knowledge graph optimization

### AEO Engine

- Answer Engine Optimization
- Structured answers
- FAQ generation
- Snippet optimization

### Social Engine

- LinkedIn, X, Instagram, Facebook, future platforms
- Channel-specific publishing adapters

### Email Engine

- Newsletter generation
- Email campaigns
- Email publishing
- Subscriber workflows

### Brand Engine

- Brand compliance
- Voice validation
- Style validation
- Terminology
- Brand governance

---

## 4. Platforms (unchanged from v2.0 law)

| Platform | Owns |
|----------|------|
| **AI Platform** | LLM routing, prompt registry, memory, embeddings, RAG, model providers, agent runtime, evaluation |
| **Automation Platform** | Scheduler, Celery, n8n, queues, events, workers, retries, webhooks — **no business logic** |
| **Shared Platform** | AuthN/AuthZ, RBAC, audit, secrets, config, storage, notifications, observability, search infra, API gateway |

OS modules consume Platforms. Platforms never own business decisions.

---

## 5. Architectural law (unchanged)

1. Business logic belongs to OS modules.
2. Infrastructure belongs to Platforms.
3. OS modules may never own infrastructure.
4. Platforms may never own business decisions.

---

## 6. Agent governance (unchanged)

```
Agent → Recommendation → Human Approval (when required)
  → Automation Platform → Execution → Audit
```

### Mandatory human gates

- Editorial approval
- Campaign launch
- Production publishing
- Brand policy changes
- Revenue-impacting automations
- Customer-facing AI policy

**Boundaries:**

- Editorial approval ≠ publish authorization
- Publishing Engine orchestration ≠ Website Engine rendering
- Website publish ≠ social / email / campaign publish

---

## 7. Publish path (destination)

```
Editorial Engine (human approve + promote attestation)
        ↓
Publishing Engine (channel selection, jobs, queue)
        ↓
   ┌────┴────┬────────────┬────────────┐
   ▼         ▼            ▼            ▼
Website   Social       Email       (other
Engine    Engine       Engine       channels)
(site only)
```

Website Engine executes **website** destination jobs only.  
Social/Email engines execute their channel adapters.  
Campaign Engine may coordinate windows/sequences across channels without owning website rendering.

---

## 8. Relationship to current implementation

| Statement | Status |
|-----------|--------|
| Current implementation remains valid | **YES** |
| Publishing Engine implementation started | **NO** |
| Website Engine code required in G1 | **NO** |
| Sprint baselines invalidated | **NO** |
| Runtime / API / DB changed by G1 | **NO** |

---

## 9. Freeze declaration

**ARCHITECTURE v2.1 FROZEN**

Ready for **M1 — Publishing Engine Phase 1** (implementation sprint; out of scope for G1).

---

## 10. Impact verification (G1)

| Dimension | Impact |
|-----------|--------|
| Architecture impact (implementation) | **NONE** |
| Runtime impact | **NONE** |
| API impact | **NONE** |
| Database impact | **NONE** |
| Code / git | **NONE** |
