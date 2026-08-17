# Founder OS Architecture v2.2

**Status:** FROZEN  
**Sprint:** A1 — Architecture v2.2 Update  
**Date:** 2026-08-10  
**Canonical repository:** `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`  
**Supersedes (destination):** Architecture v2.1 ([Architecture_v2.1.md](Architecture_v2.1.md))  
**ADR:** [Architecture_ADR_003.md](Architecture_ADR_003.md)

**Nature:** Destination architecture (governance only).  
**Does not change:** current implementation, APIs, database, runtime, or business logic.

v2.2 refinement: Marketing OS documents **shipped engines** (Content Studio, Editorial, Publishing, Website Core) and names **future engines** (Video, Newsletter, Community) without implementing them.

Related:

- [Architecture_v2_Diagram.md](Architecture_v2_Diagram.md)
- [Architecture_Principles.md](Architecture_Principles.md)
- [Platform_vs_OS_Boundaries.md](Platform_vs_OS_Boundaries.md)
- [Future_Module_Roadmap.md](Future_Module_Roadmap.md)
- [Migration_Target_Architecture.md](Migration_Target_Architecture.md)
- [Marketing_OS_v2.2.md](Marketing_OS_v2.2.md)
- [Marketing_OS.md](Marketing_OS.md) (historical v2.1)
- [Architecture_ADR_003.md](Architecture_ADR_003.md)
- [Architecture_ADR_004.md](Architecture_ADR_004.md) — Sales OS boundaries (SALES A1; additive)
- [Architecture_ADR_005.md](Architecture_ADR_005.md) — Sales OS Architecture Baseline v1.0 freeze (SALES A1.5)
- [Architecture_ADR_007.md](Architecture_ADR_007.md) — Sales Runner Deal Stage Update Baseline v1.0 freeze (SALES A3.5)
- [../sales/SALES_OS_ARCHITECTURE.md](../sales/SALES_OS_ARCHITECTURE.md)
- [../sales/SALES_OS_ARCHITECTURE_BASELINE_v1.0.md](../sales/SALES_OS_ARCHITECTURE_BASELINE_v1.0.md)
- [../sales/SALES_RUNNER_DEAL_STAGE_BASELINE_v1.0.md](../sales/SALES_RUNNER_DEAL_STAGE_BASELINE_v1.0.md)

---

## 1. Purpose

Canonical long-term architecture of **Founder OS**, refined from v2.1 to:

1. Reflect Marketing OS engines that have completed Phase-1 / Core work.
2. Add named **future** Marketing OS engines (Video, Newsletter, Community) as destination placeholders only.
3. Preserve Architectural Law: OS modules own business decisions; Platforms own infrastructure.

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
│   ├── Website Engine
│   ├── Campaign Engine
│   ├── SEO Engine
│   ├── GEO Engine
│   ├── AEO Engine
│   ├── Social Engine
│   ├── Email Engine
│   ├── Brand Engine
│   ├── Video Engine              ← FUTURE (v2.2)
│   ├── Newsletter Engine         ← FUTURE (v2.2)
│   └── Community Engine          ← FUTURE (v2.2)
├── Customer Success OS
├── Operations OS
├── Knowledge OS
├── AI Platform
├── Automation Platform
└── Shared Platform
```

---

## 3. Platforms (unchanged law)

| Platform | Owns |
|----------|------|
| **AI Platform** | LLM routing, prompt registry, memory, embeddings, RAG, model providers, agent runtime, evaluation |
| **Automation Platform** | Scheduler, Celery, n8n, queues, events, workers, retries, webhooks — **no business logic** |
| **Shared Platform** | AuthN/AuthZ, RBAC, audit, secrets, config, storage, notifications, observability, search infra, API gateway |

---

## 4. Architectural law (unchanged)

1. Business logic belongs to OS modules.  
2. Infrastructure belongs to Platforms.  
3. OS modules may never own infrastructure.  
4. Platforms may never own business decisions.

---

## 5. Agent governance (unchanged)

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

**Boundaries:** Editorial ≠ publish; Publishing orchestration ≠ Website render; Website ≠ Social/Email/Campaign.

---

## 6. Marketing OS engines — status overview

| Engine | Current implementation status | Future implementation status |
|--------|------------------------------|------------------------------|
| Content Studio | **SHIPPED** (read API + UI + kanban baselines) | Additive planning/editing surfaces |
| Editorial Engine | **SHIPPED** (readiness + Approval Phase 1) | Expand gates; never auto-publish |
| Publishing Engine | **SHIPPED** (orchestration Phase 1 + baseline freeze) | Channel adapters invoke engines; no render |
| Website Engine | **SHIPPED** (Core + Static Provider baselines) | Deploy mode decision (M4); CMS adapters later |
| Campaign Engine | **NOT STARTED** (destination named) | Launch gate + multi-channel windows |
| SEO Engine | **PARTIAL** (API/tools exist; not formal engine package) | Formalize scoring/linking under Marketing OS |
| GEO Engine | **NOT STARTED** as engine | Formalize under Marketing OS |
| AEO Engine | **NOT STARTED** as engine | Formalize under Marketing OS |
| Social Engine | **NOT STARTED** (Publishing channel stubs only) | Channel adapters |
| Email Engine | **PARTIAL** / nascent | Distinct from Newsletter Engine (see below) |
| Brand Engine | **PARTIAL** (implicit in validators) | Explicit brand policy + human gate |
| Video Engine | **FUTURE** — not implemented | Named destination only in v2.2 |
| Newsletter Engine | **FUTURE** — not implemented | Named destination; may specialize Email Engine later |
| Community Engine | **FUTURE** — not implemented | Named destination only in v2.2 |

Detailed mission / I/O / deps: [Marketing_OS_v2.2.md](Marketing_OS_v2.2.md).

---

## 7. Compatibility with shipped sprints

| Sprint / baseline | Compatible? |
|-------------------|-------------|
| Content Studio E2–E4.5 | YES |
| Editorial Readiness / E7 Approval | YES |
| Publishing Engine M1 / M1.5 | YES |
| Website Engine M2 / M2.5 / M3 / M3.5 | YES |
| Architecture v2.0 / v2.1 | YES — historical; v2.2 is current destination |
| Runtime / Toolchain baselines | YES |
| UI shell audit / hardening | YES |

**No existing sprint invalidated.** Compatibility **100%**.

---

## 8. Impact verification (A1)

| Dimension | Impact |
|-----------|--------|
| Architecture impact (running system) | **NONE** |
| Runtime impact | **NONE** |
| API impact | **NONE** |
| Database impact | **NONE** |
| Code / git | **NONE** |

---

## 9. Freeze declaration

**ARCHITECTURE v2.2 FROZEN**

Ready for **G2 — Platform Agent Registry** (governance / platform naming; out of scope for A1).
