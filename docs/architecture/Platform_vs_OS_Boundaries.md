# Platform vs OS Boundaries — Founder OS v2.2

**Status:** FROZEN  
**Sprint:** A1 (updated from G1 v2.1)  
**Date:** 2026-08-10  
**Parent:** [Architecture_v2.2.md](Architecture_v2.2.md)

Governance only. No implementation changes.

---

## 1. Boundary rule

| Concern | Owner |
|---------|-------|
| What should happen (business decision) | **OS module** |
| How AI computes / recommends | **AI Platform** (infra) + OS-owned task definitions |
| When / how jobs run | **Automation Platform** |
| Who may act / how we audit / secrets / gateway | **Shared Platform** |

---

## 2. OS inventory (destination)

| OS | Business ownership | Must not own |
|----|--------------------|--------------|
| Executive OS | Cross-OS executive decisions & KPI interpretation | LLM infra, Celery, auth stack |
| Sales OS | Prospecting, outreach, SDR workflows | Model providers, queues, RBAC engine |
| Revenue OS | CRM, deals, forecast, revenue automations (decisions) | Embedding stores as product, webhook transport |
| Marketing OS | Content lifecycle, editorial, publish orchestration, website, campaigns, SEO/GEO/AEO, brand, social, email; future video/newsletter/community | Agent runtime substrate, scheduler ownership |
| Customer Success OS | CS playbooks, account health decisions | Secrets manager, observability stack |
| Operations OS | Internal ops workflows | API gateway |
| Knowledge OS | Knowledge products & corpus policy | Raw vector DB ops as Shared/AI infra |

### Marketing OS engines (sub-boundaries) — v2.2

| Engine | Owns | Does not own | Status |
|--------|------|--------------|--------|
| Content Studio | Content planning, editing, organization | Publish auth, website render | SHIPPED |
| Editorial Engine | Review workflow, approvals, editorial governance, audit trail | Production publish, website CMS | SHIPPED |
| Publishing Engine | Publication orchestration; channels; jobs; queue | Website implementation, rendering, SEO ownership, social APIs | SHIPPED |
| Website Engine | Canonical Founder website; **website publishing only** | Campaign logic, social publishing | SHIPPED (Core + Static) |
| Campaign Engine | Scheduling, sequences, publishing windows, multi-channel coordination | Website rendering, Celery ownership | NOT STARTED |
| SEO Engine | SEO scoring, keywords, internal linking, metadata optimization | Site deploy hooks, social adapters | PARTIAL |
| GEO Engine | GEO / LLM discoverability / citation / KG optimization | Embedding infrastructure | NOT STARTED |
| AEO Engine | Structured answers, FAQ, snippet optimization | Publish queue | NOT STARTED |
| Social Engine | Channel-specific social publishing adapters | Website publishing | NOT STARTED |
| Email Engine | Email campaigns/publishing, subscribers | Website sitemap | PARTIAL |
| Brand Engine | Brand compliance, voice/style/terminology, brand governance | AuthN implementation | PARTIAL |
| Video Engine | Video content lifecycle (future) | Social platform SoT | FUTURE |
| Newsletter Engine | Newsletter product lifecycle (future) | Transactional email infra | FUTURE |
| Community Engine | Community programs / surfaces (future) | CRM deal ownership | FUTURE |

Full I/O specs: [Marketing_OS_v2.2.md](Marketing_OS_v2.2.md).

---

## 3. Platform inventory (destination)

### AI Platform

| Owns | Does not own |
|------|--------------|
| LLM routing, providers | Whether content is editorially approved |
| Prompt registry (infra) | Campaign launch |
| Memory, embeddings, RAG infra | Brand policy content |
| Agent runtime, evaluation harness | Website slug policy (Website Engine) |

**Consumers:** Marketing OS, Sales OS, Revenue OS, Knowledge OS, others.

### Automation Platform

| Owns | Does not own |
|------|--------------|
| Scheduler, Celery, n8n | Editorial / publish / campaign / website business rules |
| Queues, events, workers, retries | Approver identity policy |
| Webhooks (transport) | “Should we launch?” / “What is the canonical URL?” |

### Shared Platform

| Owns | Does not own |
|------|--------------|
| AuthN, AuthZ, RBAC | Marketing copy strategy |
| Audit storage & standards | Editorial or website decision meaning |
| Secrets, configuration | CRM domain models |
| Storage, notifications | Agent recommendations |
| Observability, search infra | Campaign creative / site HTML |
| API Gateway | OS-specific business route semantics |

---

## 4. Decision ownership matrix

| Decision | Owner | Infra helpers |
|----------|-------|---------------|
| Editorial approve / reject / request-changes | Editorial Engine | Shared audit |
| Phase-scoped promote | Editorial Engine | Filesystem/tools; not publish |
| Create publish job / choose channel | Publishing Engine | Automation for job transport |
| Website render / slug / deploy / site publish | Website Engine | Automation for deploy hooks |
| Social channel publish | Social Engine | Automation for delivery |
| Email publish | Email Engine | Automation for delivery |
| Campaign launch | Campaign Engine | Automation for execution |
| Brand policy change | Brand Engine | Shared audit |
| SEO scoring / keyword strategy | SEO Engine | AI Platform if scoring assisted |
| Revenue-impacting automation enablement | Revenue OS | Automation + Shared audit |
| Customer-facing AI policy | Policy owners + Shared Platform | AI Platform technical controls |
| Retry / backoff of a job | Automation Platform | OS defines idempotency needs |

---

## 5. Conflation traps (forbidden)

| Trap | Why forbidden |
|------|----------------|
| Revenue OS `/approvals` = Editorial Approval | Different domains |
| Readiness PASS = approved | Readiness observational |
| Editorial Approved = publish authorized | FDR-003 |
| Publishing Engine owns HTML/sitemap/WordPress | v2.1 → Website Engine |
| Website Engine owns campaigns or social | v2.1 boundaries |
| SEO Engine owns website deploy | Deploy hooks → Website Engine |
| Crew kickoff = human gate satisfied | Agents recommend only |
| Celery task encodes brand/website policy | Business logic in Automation |

---

## 6. Compatibility with shipped sprints

| Sprint / baseline | Boundary fit |
|-------------------|--------------|
| Content Studio read + kanban | Content Studio — compatible |
| Editorial Readiness / Approval E7 | Editorial Engine — compatible |
| Runtime / Architecture baselines v1.x | As-is; v2.1 destination — compatible |
| Toolchain Baseline v1.0 | Shared Platform — compatible |
| Publishing Engine implementation | **Not started** — safe refinement |
| Website Engine | Docs only in G1 — zero code |

No sprint is invalidated.

---

## 7. Change control

Moving a capability across OS ↔ Platform or across Publishing ↔ Website requires:

1. Amendment to Architecture_v2.1.md (or superseding ADR)
2. Update to this boundary matrix
3. Explicit implementation sprint (not G1)
