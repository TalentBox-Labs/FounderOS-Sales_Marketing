# Founder OS Commercial Operating System — Master Architecture v1

**STATUS:** ARCHITECTURE / GOVERNANCE ONLY  
**Sprint:** COS-ARCH-v1  
**Branch:** `founder-os-architecture-v1`  
**HEAD / baseline:** `a7463e5e6bb8785749c6f5faab972e75dccc6b5f` (`founder-os-demo-runtime-v1.0`)  
**Nature:** Documentation. Does not change production code, templates, models, migrations, or tests.

Parent frozen law (still binding): [Architecture v2.2](../../../architecture/Architecture_v2.2.md), [ADR-004](../../../architecture/Architecture_ADR_004.md), [ADR-005](../../../architecture/Architecture_ADR_005.md), Sales / Revenue orchestration / UI-D1.5 / UI-D2 / SaaS S1–S4 baselines.

---

## 0. Repository grounding

| Check | Result |
|-------|--------|
| Branch | `founder-os-architecture-v1` |
| HEAD | `a7463e5` — stabilize Founder OS demo runtime bootstrap |
| Tag | `founder-os-demo-runtime-v1.0` points at this commit |
| Working tree | Clean at audit time (docs in this sprint are additive) |
| Primary process | `uvicorn runner_api:app` |
| Canonical UI shell | Jinja `templates/` + `runner_api_routers/ui.py` |
| Physical packages | Commercial code lives under `revenue_os/` (ACCEPTED_LEGACY colocation, not ownership proof) |

This pack **does not replace** Architecture v2.2. It defines the **commercial operating system** view of Founder OS: how Sales, Marketing, and Revenue domains coordinate inside one product.

### Prompt vs repository conflicts (reported, not forced)

| Prompt assumption | Repository reality | Resolution in this pack |
|-------------------|--------------------|-------------------------|
| Sales OS owns Opportunities as a distinct graph node | Frozen Sales domain: **Opportunity is an alias of Revenue `Deal`** | Alias language in UI; one SoT (`deals`) |
| Lead is a first-class entity | **Lead is an alias of `Contact` + status/events** | No `leads` table |
| Company is the tenant | **`Organization` is tenant; `Company` is CRM account** | Never conflate |
| Four products | One product; three commercial domains + Founder synthesis | Founder OS is the OS |
| Greenfield event names (`LEAD_CREATED`, …) | Existing `AgentActionLog.action_type` + approvals + workflow keys | Catalog maps **existing** types; proposed names are *canonical overlay*, not a rewrite |
| Full Sales/Marketing/Revenue primary nav | Frozen UI-D1.5 primary nav is Command / Demand / Approvals / Activity / Revenue Workflow | Progressive disclosure; conceptual model ≠ shipping IA |
| Architecture v2.2 Executive/CS/Ops OS as peers | Still destination law; Founder UI today is a **commercial slice**, not the full v2.2 tree | COS pack scopes commercial domains; does not delete CS/Ops/Knowledge |
| MDG0 product target: not multi-tenant | SaaS S1–S4 **implemented** `IdentityContext`, `TenantContext`, `Organization` | Tenancy is live constraint; MDG0 remains historical product-intent evidence |
| Sales↔Marketing contract: QualifiedDemand `NOT_IMPLEMENTED` | `qualified_demand_service.py` (MC04) **is implemented** | Treat MC04 as LIVE intake; A1.5 contract text is stale on implementation status |
| Hosted single-user as exclusive model | Tenant columns + org cookie exist; one deployment can host multiple orgs | Preserve tenant isolation; product packaging (single-founder vs SaaS) is a later commercial decision |

---

## 1. Product thesis

**Founder OS is one commercial operating system.**

Sales OS, Marketing OS, and Revenue OS are **coordinated domains**, not separate products, not separate tenants, and not separate CRMs.

Operating loop (customer language):

```
UNDERSTAND → DECIDE → EXECUTE → GOVERN → LEARN
```

Founder questions the product must answer:

| Question | Domain contribution |
|----------|---------------------|
| What changed? | Activity + provenance (`Activity`, `AgentActionLog`) |
| What matters now? | Founder Home / Command attention |
| What is at risk? | Pipeline, follow-up stop, stale booking, deal risk flags |
| What should happen next? | Advisory recommendations (never silent CRM truth) |
| What has AI handled? | AI Work / proposal queue |
| What requires founder authority? | Approvals |
| What commercial outcome resulted? | `Deal` + `CommercialOutcome` handoff |
| What has the system learned? | Derived intelligence; never auto-promoted to company truth |

Customer-facing language must not lead with `TenantContext`, `SoT`, milestone codes, or worker names. Those remain engineering evidence.

---

## 2. Preserved governed baselines

Do not weaken:

- `TenantContext` / `IdentityContext`
- `WorkflowOrchestrator` revenue workflows (M1–M4)
- `ApprovalRequest` human gate
- Proposal-only AI; human-gated outbound
- Governed follow-up, reply, meeting booking
- Execution-time revalidation; stale-slot containment; idempotency
- Activity / provenance
- Cross-tenant protection
- Contact / Deal authority
- Calendar credential isolation (`OrganizationIntegrationBinding`)

Frozen tests and attestations are **evidence**. This pack does not rewrite them.

---

## 3. Canonical structure (commercial view)

```
Founder OS  (one product)
├── Founder synthesis     Home, Approvals, AI Work, Activity, Company Context
├── Marketing OS          discover → demand (content engines remain Marketing-owned)
├── Sales OS              research → engage → meeting → deal ops
├── Revenue OS            CRM entity SoT, forecast, commercial recording
├── AI Platform           models, agents runtime (no commercial SoT)
├── Automation Platform   transport, schedules (no business decisions)
└── Shared Platform       identity, tenant, secrets, audit infra
```

Architecture v2.2 modules (Customer Success, Operations, Knowledge, Executive OS) remain destination peers. They are **out of COS-1 shipping scope** except where they already leak into the commercial graph (`Client`/`Project`, Hermes `Goal`, recruitment `Candidate`).

---

## 4. Authority law (commercial)

```
AI / worker → recommendation or ApprovalRequest
  → human decision (session-bound)
  → domain service (revalidates tenant + authority + freshness)
  → mutation of canonical SoT
  → AgentActionLog / Activity provenance
```

UI must not: invent eligibility, invent availability, set `requested_by` / `decided_by`, or mutate Contact/Deal/calendar directly.

---

## 5. Artifact index

| Artifact | Purpose |
|----------|---------|
| [FOUNDER_OS_PRODUCT_HIERARCHY_v1.md](FOUNDER_OS_PRODUCT_HIERARCHY_v1.md) | Canonical navigation after audit |
| [FOUNDER_OS_COMMERCIAL_GRAPH_v1.md](FOUNDER_OS_COMMERCIAL_GRAPH_v1.md) | Entities, aliases, SoT |
| [FOUNDER_OS_DOMAIN_OWNERSHIP_MATRIX_v1.md](FOUNDER_OS_DOMAIN_OWNERSHIP_MATRIX_v1.md) | Domain boundaries |
| [FOUNDER_OS_COMMERCIAL_EVENT_CONTRACT_v1.md](FOUNDER_OS_COMMERCIAL_EVENT_CONTRACT_v1.md) | Existing + overlay events |
| [FOUNDER_OS_FOUNDER_PROFILE_CONTEXT_v1.md](FOUNDER_OS_FOUNDER_PROFILE_CONTEXT_v1.md) | Operating context layers |
| [FOUNDER_OS_EXPERIENCE_ARCHITECTURE_v1.md](FOUNDER_OS_EXPERIENCE_ARCHITECTURE_v1.md) | UX / terminology |
| [FOUNDER_OS_BACKEND_EXPERIENCE_CONTRACT_v1.md](FOUNDER_OS_BACKEND_EXPERIENCE_CONTRACT_v1.md) | Screen ↔ read model |
| [FOUNDER_OS_INTERNATIONAL_UI_REQUIREMENTS_v1.md](FOUNDER_OS_INTERNATIONAL_UI_REQUIREMENTS_v1.md) | Design-system requirements |
| [FOUNDER_OS_COS1_VERTICAL_SLICE_v1.md](FOUNDER_OS_COS1_VERTICAL_SLICE_v1.md) | First integrated journey |
| [FOUNDER_OS_CONTROLLED_PARALLELISM_MODEL_v1.md](FOUNDER_OS_CONTROLLED_PARALLELISM_MODEL_v1.md) | Streams A/B/C |
| [FOUNDER_OS_ARCHITECTURE_CONFLICT_AUDIT_v1.md](FOUNDER_OS_ARCHITECTURE_CONFLICT_AUDIT_v1.md) | Debt register |
| [FOUNDER_OS_COS_ROADMAP_v1.md](FOUNDER_OS_COS_ROADMAP_v1.md) | Sequence |
| [FOUNDER_OS_COS_ARCH_BASELINE_MANIFEST_v1.md](FOUNDER_OS_COS_ARCH_BASELINE_MANIFEST_v1.md) | Freeze inventory |

---

## 6. Frontend direction (summary)

**HYBRID:** Keep Jinja Founder shell for the commercial loop (already live UI-D1/D2). Evolve information architecture and design tokens in that shell. Do not migrate the product to a new SPA to “modernize.” Unmounted React `/app` remains RETAIN_AND_REFACTOR_LATER per Sales CRM UI disposition.

---

## 7. COS-1 thesis (summary)

Do **not** start COS-1 by rebuilding Marketing ICP from scratch.

The repository already has a governed commercial spine:

QualifiedDemand → Contact → research/outreach → follow-up → reply → booking → Approval → Deal/outcome path.

COS-1 should **stabilize that spine** as the Founder journey (terminology, company context stub, event overlay, read-model completeness) and attach Marketing engines later (COS-2).
