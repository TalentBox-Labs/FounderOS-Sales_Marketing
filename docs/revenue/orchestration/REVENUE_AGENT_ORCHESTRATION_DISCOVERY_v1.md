# Revenue Agent Orchestration Discovery v1

**Status:** DISCOVERY ARTIFACT (NOT a frozen baseline)  
**Date:** 2026-08-17  
**Mode:** Repository-grounded architecture audit only  
**Scope:** Determine Founder OS-native architecture for future Revenue Agent Orchestration without creating parallel business SoTs or bypassing frozen contracts (S1.5–S4.5, MC04.5, MC06.5, A1.5, A3.5, A4.5, MDG1.5, UI2.5, OF1.5)

---

## 1. Executive Summary

Founder OS already implements a **human-gated revenue loop** with canonical CRM SoTs (`Contact`, `Deal`, `Company`, `Activity`), contract-based handoff objects (`QualifiedDemand`, `CommercialOutcome` persisted as `AgentActionLog` audit records), and **proposal-only AI capabilities** that never mutate domain state directly.

The repository does **not** support seven autonomous AI agents as a native architecture. Instead, evidence shows:

| Layer | What exists |
|-------|-------------|
| **SoT** | `Contact`, `Deal`, `Company`, `Activity` (SQLAlchemy); `QualifiedDemand` / `CommercialOutcome` (Pydantic contracts → `AgentActionLog`) |
| **Orchestration** | `WorkflowOrchestrator`, `EventBus`, `HeartbeatScheduler`, `HermesPlanner`, `GoToMarketOrchestrator`, n8n bridge |
| **AI** | `AIService` (OpenAI wrapper, env-backed), 5 `sales_agents` modules (draft → `ApprovalRequest`) |
| **Authority** | `require_human_mutation_authority()`, frozen A3/A4/MDG/MC04/MC06 gates |
| **Tenancy** | `TenantContext`, org-scoped CRM, org-scoped connector credentials (S4.5 frozen) |

**Recommendation:** Extend the existing **workflow + human-approval + domain-service mutation** pattern. Use **zero to two true AI reasoning nodes** (research draft, message draft). Do **not** introduce seven autonomous agents or a parallel revenue SoT.

**Recommended MVP:** Contact (existing) → enrich/research → AI draft → human approval → scheduled Activity or n8n handoff → audit — all within existing SoTs and frozen authority contracts.

---

## 2. Repository Evidence Inventory

### 2.1 Demand & Prospect Entry

| Component | Path | Symbol | Responsibility |
|-----------|------|--------|----------------|
| Manual demand registration | `runner_api_routers/manual_demand.py` | `POST /api/manual-demand/register` | Human registers inbound demand; MDG1.5 contract |
| Marketing handoff | `revenue_os/services/qualified_demand_service.py` | `register_marketing_handoff()` | Creates `QualifiedDemand` audit record (MC04.5) |
| Public/inbound webhook | `runner_api_routers/n8n_webhooks.py` | `POST /api/webhooks/n8n/inbound` | Tenant-bound inbound events (S4.5) |
| Prospecting import | `runner_api_routers/prospecting.py` | prospecting routes | Import contacts from scraper/Apollo MCP |
| Lead prospecting | `revenue_os/services/lead_prospecting_service.py` | `import_prospects()`, `provider_status()` | Deterministic prospect import with env limits |

### 2.2 CRM Canonical Objects

| Object | Path | Model | SoT? |
|--------|------|-------|------|
| Contact | `revenue_os/models/contact.py` | `Contact`, `ContactStatus`, `ContactSource` | **YES** |
| Deal | `revenue_os/models/deal.py` | `Deal`, `DealStage` | **YES** |
| Company | `revenue_os/models/contact.py` | `Company` | **YES** |
| Activity | `revenue_os/models/activity.py` | `Activity`, `ActivityType`, `SequenceStep` | **YES** (timeline) |
| QualifiedDemand | `revenue_os/services/qualified_demand_service.py` | Pydantic contract | Audit contract (AgentActionLog) |
| CommercialOutcome | `revenue_os/services/commercial_outcome_service.py` | Pydantic contract | Audit contract (AgentActionLog) |

### 2.3 CRM Routes (Frozen S3.5 — 15 routes)

| Router | Path | Routes |
|--------|------|--------|
| CRM API | `runner_api_routers/crm.py` | 7 read + 8 mutation; all org-scoped via `TenantContext` |

Key mutations: contact create/update/status, deal create/stage, activity create, company update.

### 2.4 Pipeline & Revenue State

| Component | Path | Responsibility |
|-----------|------|----------------|
| Deal automation | `revenue_os/services/deal_automation_service.py` | `create_deal_from_contact()`, stage suggestions |
| Lead scoring | `revenue_os/services/lead_scoring_service.py` | Score suggestion (non-mutating) |
| Pipeline health | `revenue_os/services/pipeline_health.py` | Read-model aggregation |
| Contact status (A4) | `revenue_os/services/contact_status_service.py` | Human-gated status transitions |
| Deal stage (A3) | Frozen in `mutation_authority.py` | Human-gated stage transitions |

### 2.5 Research & Enrichment

| Component | Path | Responsibility |
|-----------|------|----------------|
| LinkedIn enrichment | `revenue_os/services/linkedin_enrichment.py` | Proxycurl API enrichment |
| ICP research agent | `revenue_os/services/sales_agents.py` | `AGENT_ICP_RESEARCH` — draft only |
| CRM enrich route | `runner_api_routers/crm.py` | `POST .../enrich` |

### 2.6 Messaging & Outreach

| Component | Path | Responsibility |
|-----------|------|----------------|
| AI service | `revenue_os/services/ai_service.py` | OpenAI `_chat()`, template fallback |
| Sales agents (5) | `revenue_os/services/sales_agents.py` | Draft proposals → `ApprovalRequest` |
| Outreach sequences | `revenue_os/services/outreach_service.py` | Schedule Activities from sequence steps |
| Outreach router | `runner_api_routers/outreach.py` | Sequence enrollment API |
| Approvals | `revenue_os/services/approvals.py` | Propose → human decide → execute (n8n) |

### 2.7 Follow-Up & Scheduling

| Component | Path | Responsibility |
|-----------|------|----------------|
| Follow-up engine | `revenue_os/services/followups.py` | Overdue tasks, stalled contacts, at-risk deals |
| Activity scheduling | `revenue_os/models/activity.py` | `scheduled_at`, `due_date` on Activity |
| Heartbeat scheduler | `revenue_os/scheduler.py` | `HeartbeatScheduler` — deterministic jobs |
| n8n meeting.booked | `runner_api_routers/n8n_webhooks.py` | Inbound meeting signal (recommendation only) |

### 2.8 Integrations & Connectors

| Component | Path | Responsibility |
|-----------|------|----------------|
| Connector credentials | `revenue_os/models/integrations.py` | `ConnectorCredentialRecord`, org ownership |
| Credentials vault | `revenue_os/services/credentials_vault.py` | `load_credentials(org, allow_global_fallback=False)` |
| Tenant resolution | `revenue_os/services/integration_tenant_resolution.py` | Webhook tenant binding |
| n8n integration | `revenue_os/integrations/n8n.py` | `trigger_workflow()`, EventBus bridge |
| OpenAI | `revenue_os/services/ai_service.py` | Env `OPENAI_API_KEY` (GLOBAL_BY_DESIGN) |

### 2.9 Agent & Orchestration Infrastructure

| Component | Path | Responsibility |
|-----------|------|----------------|
| Agent coordinator | `revenue_os/agents/orchestration.py` | `AgentCoordinator`, `WorkflowOrchestrator`, `seed_platform_agents()` |
| Platform agents | Same | heartbeat, hermes, copilot, workflow_engine, n8n_bridge + 5 sales draft agents |
| SDR agent | `revenue_os/agents/sdr_agent.py` | CrewAI wrapper |
| Recruiter agent | `revenue_os/agents/recruiter_agent.py` | CrewAI wrapper |
| Event bus | `revenue_os/automation/events.py` | `EventBus` pub/sub |
| Hermes planner | `revenue_os/services/hermes_planner.py` | Goal-driven automation planning |
| GTM orchestrator | `revenue_os/services/go_to_market_orchestrator.py` | Go-to-market workflow coordination |

### 2.10 Identity, Tenancy & Audit

| Component | Path | Responsibility |
|-----------|------|----------------|
| TenantContext | `revenue_os/services/tenant_context.py` | Server-derived org scope |
| Mutation authority | `revenue_os/services/mutation_authority.py` | `require_human_mutation_authority()` |
| Human approver | `src/tools/editorial_approval.py` | `is_human_approver()` |
| Agent action log | `revenue_os/services/activity_log.py` | `log_agent_action()` — audit provenance |
| requested_by | Frozen S1.5 | Server-bound; spoof blocked |

### 2.11 Operator / Cockpit (Read Models)

| Component | Path | Responsibility |
|-----------|------|----------------|
| Cockpit read model | `revenue_os/services/cockpit_read_model.py` | Dashboard projection |
| Operator flow | `runner_api_routers/operator_flow.py` | Operator workflow UI backend |
| Operator read model | `revenue_os/services/operator_flow_read_model.py` | Flow state projection |

### 2.12 Frozen Documentation Contracts

| Contract | Path |
|----------|------|
| MC04.5 Qualified Demand | `docs/integration/mc04_5/` |
| MC06.5 Commercial Outcome | `docs/integration/mc06_5/` |
| S4.5 Integration Tenant Isolation | `docs/saas/S4_5_INTEGRATION_TENANT_ISOLATION_BASELINE_v1.md` |
| Sales Revenue Contract | `docs/sales/SALES_REVENUE_CONTRACT.md` |

---

## 3. Current Revenue Domain Map

### 3.1 Canonical Flow (Evidence-Backed)

```
[Marketing / Manual Demand / Prospecting Import / n8n Inbound]
   ↓ register / import
[QualifiedDemand contract → AgentActionLog]  OR  [Contact direct create (CRM)]
   ↓ accept_qualified_demand (HUMAN or SERVICE with policy)
[Contact] ← canonical person SoT
   ↓ enrich (SERVICE), score (SERVICE, suggest only)
[Contact + enrichment metadata]
   ↓ apply_contact_status_update (HUMAN_ONLY — A4 frozen)
[Contact.status = QUALIFIED | REJECTED | ...]
   ↓ create_deal_from_contact (SERVICE propose, HUMAN approve via ApprovalRequest)
[Deal] ← canonical opportunity SoT
   ↓ apply_deal_stage_update (HUMAN_ONLY — A3 frozen)
[Deal.stage progression]
   ↓ closed-won
[CommercialOutcome contract → AgentActionLog] (MC06.5)
   ↓ accept_commercial_outcome (HUMAN)
[Revenue recorded / handoff complete]
```

### 3.2 Answers to Discovery Questions

| # | Question | Answer (Repository Term) |
|---|----------|--------------------------|
| 1 | Initial demand/prospect intent | `QualifiedDemand` (audit contract) OR direct `Contact` create via CRM/prospecting |
| 2 | Canonical Contact | `Contact` model — `revenue_os/models/contact.py` |
| 3 | Canonical Company/Account | `Company` model — same file |
| 4 | Canonical Deal | `Deal` model — `revenue_os/models/deal.py` |
| 5 | QualifiedDemand | Pydantic contract persisted as `AgentActionLog`; NOT a DB table |
| 6 | CommercialOutcome | Pydantic contract persisted as `AgentActionLog`; NOT a DB table |
| 7 | Pipeline progression | `Deal.stage` + `Contact.status`; human-gated (A3/A4) |
| 8 | State mutators | CRM routes, `qualified_demand_service`, `commercial_outcome_service`, `deal_automation_service`, `contact_status_service` |
| 9 | Shared business SoTs | `Contact`, `Deal`, `Company`, `Activity` |
| 10 | Projections only | `cockpit_read_model`, `operator_flow_read_model`, `pipeline_health`, lead score suggestions |
| 11 | Trusted human authority | Contact status (A4), deal stage (A3), QD accept/reject, CO handoff/accept/reject, approval queue decisions |
| 12 | Service/agent/AI may perform | Enrichment, scoring suggestions, draft generation, QD registration (service), activity scheduling |
| 13 | AI/agent prohibited | Direct Contact.status, Deal.stage, QD accept, CO accept, credential access without org scope |
| 14 | Audit/provenance | `AgentActionLog` via `log_agent_action()`; CRM audit fields; `ApprovalRequest` transitions |

### 3.3 Parallel Path: Outreach Loop (Non-Mutating State)

```
[Contact]
   ↓ sales_agents.* (AI draft)
[ApprovalRequest — pending]
   ↓ human approve
[n8n trigger_workflow("send-email")] OR [Activity scheduled]
   ↓ inbound n8n webhook
[Activity / recommendation surfaced to operator]
```

---

## 4. Current AI / Agent Architecture

### 4.1 Inventory

| Name | Module | Type | Purpose | Provider | Sync/Async | Mutation Authority |
|------|--------|------|---------|----------|------------|-------------------|
| AIService | `ai_service.py` | LLM wrapper | Text generation | OpenAI (env key) | Sync | **None** — returns text |
| AGENT_ICP_RESEARCH | `sales_agents.py` | AI-assisted service | Research draft | Via AIService | Sync | **None** — files ApprovalRequest |
| AGENT_COLD_EMAIL | `sales_agents.py` | AI-assisted service | Email draft | Via AIService | Sync | **None** |
| AGENT_LINKEDIN_OPENER | `sales_agents.py` | AI-assisted service | LinkedIn draft | Via AIService | Sync | **None** |
| AGENT_FOLLOWUP_SEQUENCE | `sales_agents.py` | AI-assisted service | Follow-up draft | Via AIService | Sync | **None** |
| AGENT_OBJECTION_HANDLER | `sales_agents.py` | AI-assisted service | Objection draft | Via AIService | Sync | **None** |
| AgentCoordinator | `orchestration.py` | Registry/coordinator | Agent registration, heartbeat | N/A | Sync | Registry only |
| WorkflowOrchestrator | `orchestration.py` | Workflow engine | Multi-step workflow dispatch | N/A | Sync | Delegates to services |
| HeartbeatScheduler | `scheduler.py` | Scheduled task | Periodic deterministic jobs | N/A | Async (cron) | Job-dependent |
| HermesPlanner | `hermes_planner.py` | Planning service | Goal → action plan | Optional LLM | Sync | Plan only |
| n8n_bridge | `integrations/n8n.py` | Connector adapter | Outbound webhooks | n8n | Sync HTTP | External side effects via n8n |
| SDR Agent | `sdr_agent.py` | CrewAI crew | SDR workflow wrapper | CrewAI/OpenAI | Sync | **Unknown** — legacy path |
| Recruiter Agent | `recruiter_agent.py` | CrewAI crew | Recruiting wrapper | CrewAI/OpenAI | Sync | **Unknown** — legacy path |
| EventBus | `automation/events.py` | Event pub/sub | Decoupled automation triggers | N/A | Sync | None — emits events |
| GoToMarketOrchestrator | `go_to_market_orchestrator.py` | Orchestrator | GTM workflow coordination | N/A | Sync | Coordinates services |

### 4.2 Classification of "Agents"

| Label in repo | Actual category |
|---------------|-----------------|
| 5 sales_agents | **AI-assisted services** (proposal generators) |
| AgentCoordinator | **Registry / UI abstraction** |
| WorkflowOrchestrator | **Workflow engine** |
| n8n_bridge | **Connector adapter** |
| HeartbeatScheduler | **Scheduled task runner** |
| SDR/Recruiter CrewAI | **LLM reasoning units** (legacy, less governed) |
| HermesPlanner | **Planning service** (may use LLM) |

### 4.3 Existing Orchestration Abstraction

**YES — extend rather than replace:**

- `WorkflowOrchestrator` + `EventBus` + `HeartbeatScheduler` form the native orchestration stack
- Human approval gate via `ApprovalRequest` + `approvals.py`
- Domain mutation exclusively through CRM services with `require_human_mutation_authority()`

There is **no** need for a second orchestration framework. Future work should add **workflow steps** and **reasoning nodes** to this stack.

---

## 5. Seven-Capability Gap Analysis

### A. FIND

| Criterion | Assessment |
|-----------|------------|
| Equivalent exists? | **YES** — `lead_prospecting_service.py`, `prospecting.py`, `manual_demand.py` |
| SoT | `Contact` on import; `QualifiedDemand` for marketing handoff |
| Frozen constraints | MDG1.5, MC04.5 |
| LLM required? | **NO** — deterministic import/scrape |
| External integration? | Optional Apollo MCP, scraper (env-backed) |
| Human approval? | Import is operator-initiated |
| Mutates revenue state? | Creates Contact (CRM mutation) |
| Identity | HUMAN or SERVICE |
| **Classification** | **EXISTING_CAPABILITY** (+ deterministic prospecting) |

### B. RESEARCH

| Criterion | Assessment |
|-----------|------------|
| Equivalent exists? | **YES** — `linkedin_enrichment.py`, `sales_agents.research_contact`, CRM enrich |
| SoT | Enrichment metadata on Contact |
| LLM required? | **Optional** — Proxycurl is deterministic; ICP narrative benefits from LLM |
| Human approval? | Not required for enrichment read |
| Mutates revenue state? | Updates Contact fields |
| **Classification** | **HYBRID** (deterministic enrichment + optional AI_ASSISTED narrative) |

### C. PERSONALIZE

| Criterion | Assessment |
|-----------|------------|
| Equivalent exists? | **YES** — `sales_agents.py` (cold email, LinkedIn opener), `ai_service.py` |
| SoT | Draft in `ApprovalRequest.payload` |
| LLM required? | **YES** for quality personalization |
| Human approval? | **REQUIRED** — drafts go to ApprovalRequest |
| Mutates revenue state? | **NO** until approved |
| **Classification** | **AI_ASSISTED_SERVICE** |

### D. OUTREACH

| Criterion | Assessment |
|-----------|------------|
| Equivalent exists? | **YES** — `approvals.py`, `outreach_service.py`, n8n `send-email` |
| SoT | Activity timeline + n8n handoff |
| Human approval? | **REQUIRED** — `_execute_send_outreach_email` only on approval |
| External side effects? | **YES** — n8n email delivery |
| Mutates revenue state? | Creates Activity; may trigger Contact status change (human-gated) |
| **Classification** | **HYBRID** (ApprovalRequest gate + n8n connector) |

### E. FOLLOW-UP

| Criterion | Assessment |
|-----------|------------|
| Equivalent exists? | **YES** — `followups.py`, `outreach_service.schedule_contact_sequence`, Activity model |
| SoT | Activity (scheduled tasks) |
| Scheduling? | **YES** — `scheduled_at`, `due_date` |
| LLM required? | **Optional** — AGENT_FOLLOWUP_SEQUENCE for draft only |
| Human approval? | Recommended for outbound; scheduled Activities are operator-visible |
| **Classification** | **WORKFLOW_STATE_MACHINE** + **SCHEDULED_WORKFLOW** |

### F. BOOK

| Criterion | Assessment |
|-----------|------------|
| Equivalent exists? | **PARTIAL** — n8n inbound `meeting.booked` webhook |
| SoT | Activity or operator recommendation |
| Auto-qualify? | **NO** — repository explicitly human-gates qualification |
| External integration? | Calendar via n8n (not native) |
| **Classification** | **HUMAN_ACTION** + n8n signal (WORKFLOW for inbound event) |

### G. CLOSE / PIPELINE MANAGEMENT

| Criterion | Assessment |
|-----------|------------|
| Equivalent exists? | **YES** — A3 deal stage, A4 contact status, `commercial_outcome_service` |
| SoT | Deal, Contact, CommercialOutcome audit |
| Human approval? | **REQUIRED** for stage/status (frozen) |
| LLM required? | **NO** |
| **Classification** | **EXISTING_CAPABILITY** (human-operated + frozen contracts) |

---

## 6. Authority & Mutation Matrix

Legend: **A**=ALLOWED, **AWP**=ALLOWED_WITH_POLICY, **RHA**=REQUIRES_HUMAN_APPROVAL, **P**=PROHIBITED, **NI**=NOT_IMPLEMENTED, **U**=UNKNOWN

| Operation | HUMAN | SERVICE | AGENT | AI |
|-----------|-------|---------|-------|-----|
| Discover prospect | A | AWP | AWP | P |
| Create demand (QD) | A | AWP | AWP | P |
| Create contact | A | AWP | RHA | P |
| Enrich contact | A | A | A | A (no direct DB write) |
| Modify company | A | AWP | RHA | P |
| Qualify demand (QD accept) | A | AWP | RHA | P |
| Generate research | A | A | A | A |
| Generate message | A | A | A | A |
| Approve message | A | P | P | P |
| Send message | A | RHA | RHA | P |
| Schedule follow-up | A | A | AWP | P |
| Cancel follow-up | A | A | AWP | P |
| Book meeting | A | NI | NI | P |
| Modify deal | A | RHA | RHA | P |
| Advance pipeline (stage) | A | P | P | P |
| Create QualifiedDemand | A | AWP | AWP | P |
| Create CommercialOutcome | A | AWP | RHA | P |
| Mark won/lost | A | P | P | P |
| Access connector credential | A | AWP (org-scoped) | AWP | P |
| Invoke outbound connector | A | RHA | RHA | P |

**Evidence:**
- A3/A4: `mutation_authority.py`, frozen baseline docs
- QD/CO: `qualified_demand_service.py`, `commercial_outcome_service.py` — human gates on accept
- Approvals: `approvals.py` — `_execute_send_outreach_email` only after human approval
- Credentials: `credentials_vault.py` — org-scoped, `allow_global_fallback=False` default
- AI prohibited from mutation: architectural principle enforced by absence of AI write paths + human gates

---

## 7. Tenancy Threat Model

| # | Threat | Current Protection | Evidence | Remaining Gap | Future Requirement |
|---|--------|-------------------|----------|---------------|-------------------|
| 1 | Foreign organization_id | TenantContext server-derived | `tenant_context.py`, CRM routes | Background job context loss | Propagate TenantContext to all async jobs |
| 2 | Foreign contact_id | CRM queries org-filtered | `runner_api_routers/crm.py` | ID-only lookup paths | Always join org scope |
| 3 | Foreign deal_id | Same as contact | S3.5 frozen tests | Legacy `main.py` paths | Deprecate unscoped API |
| 4 | Connector-name-only resolution | Blocked S4 | `credentials_vault.py` | Env-backed connectors bypass DB | Tenant-bind env connectors or document GLOBAL_BY_DESIGN |
| 5 | GLOBAL_BY_DESIGN credential fallback | Disabled by default | `allow_global_fallback=False` | Legacy NULL org_id creds | Migration completion |
| 6 | AI tool args with tenant IDs | No AI tool calling yet | N/A | **HIGH** if tool calling added | Never trust AI-supplied tenant IDs |
| 7 | Webhook payload selects tenant | Blocked S4.5 | `integration_tenant_resolution.py` | Misconfigured bindings | Binding audit |
| 8 | Impersonate human requested_by | Blocked S1.5 | Server-bound requested_by | Service identity confusion | Explicit identity type in audit |
| 9 | Background task loses TenantContext | Partial | Scheduler jobs | **MEDIUM** | Job envelope with org_id |
| 10 | Retry after membership change | Not implemented | N/A | **HIGH** for scheduled outreach | Re-validate authority on execution |
| 11 | Scheduled follow-up after authority loss | Not validated | `followups.py` reads only | **MEDIUM** | Authority check before send |
| 12 | AI direct domain mutation | Prohibited by design | No AI write paths | CrewAI legacy paths | Audit/disable legacy agents |
| 13 | Cross-org action chains | No chain abstraction | N/A | Low today | Prohibit multi-tenant workflows |
| 14 | Foreign IDs in connector response | Not validated | n8n responses trusted | **MEDIUM** | Validate IDs against org scope |

---

## 8. OpenAI / LLM Boundary

### 8.1 Current Usage

| Aspect | Implementation |
|--------|----------------|
| Client wrapper | `revenue_os/services/ai_service.py` — `_chat()` |
| Configuration | `OPENAI_API_KEY` env var (GLOBAL_BY_DESIGN — not tenant-scoped) |
| Credential source | Environment only (MEDIUM documented risk per S4.5) |
| Prompt architecture | Inline prompts in `sales_agents.py`, `ai_service.py` |
| Structured output | Limited — mostly free text |
| Tool/function calling | **NOT IMPLEMENTED** in revenue path |
| Retry | Basic try/except with template fallback |
| Logging | Standard Python logging |
| Token/cost tracking | **NOT IMPLEMENTED** |
| Provenance | None on AI outputs today |
| PII handling | **NOT EXPLICIT** — sends contact context to OpenAI |
| Error handling | Falls back to template strings when unconfigured |

### 8.2 Principle Evaluation: AI PROPOSES → POLICY DECIDES → DOMAIN MUTATES → AUDIT

| Layer | Supported? | Gap |
|-------|------------|-----|
| AI proposes | **YES** — sales_agents return drafts | Need structured proposal schema |
| Policy decides | **PARTIAL** — ApprovalRequest + mutation_authority | No unified policy engine |
| Domain mutates | **YES** — CRM services | Clear |
| Audit records | **PARTIAL** — AgentActionLog for contracts; weak for AI drafts | Log model, prompt hash, input refs |

**Missing for full support:**
1. AI output provenance (model, prompt version, input entity refs)
2. Token/cost tracking per org
3. Tenant-scoped LLM credential strategy
4. Structured proposal schema (not free text → ApprovalRequest)
5. Explicit prohibition of LLM tool calling against domain APIs without human gate

---

## 9. Architecture Options

### Option A: Seven Specialized Autonomous AI Agents

| Criterion | Score |
|-----------|-------|
| Architectural fit | **POOR** — contradicts human-gated A3/A4/MC04/MC06 |
| Reuse | Low — would duplicate sales_agents |
| Tenant safety | **RISK** — autonomous mutation bypass |
| Authority safety | **FAIL** — frozen contracts prohibit |
| Operational complexity | Very high |
| Frozen-contract impact | **Violates** A3, A4, MC04.5, MC06.5 |

**Verdict:** NOT RECOMMENDED

### Option B: Single Revenue Orchestrator + Deterministic Domain Capabilities

| Criterion | Score |
|-----------|-------|
| Architectural fit | **GOOD** — aligns with WorkflowOrchestrator |
| Reuse | High — EventBus, scheduler, CRM services, approvals |
| Tenant safety | Good — orchestrator passes TenantContext |
| Authority safety | Good — human gates preserved |
| Testability | High |
| New abstractions | Revenue workflow definition (steps, not agents) |

**Verdict:** RECOMMENDED (primary)

### Option C: Workflow/State-Machine + Selective AI Reasoning Nodes

| Criterion | Score |
|-----------|-------|
| Architectural fit | **EXCELLENT** — matches ApprovalRequest pattern |
| Reuse | Highest — sales_agents become reasoning nodes |
| Tenant safety | Good |
| Authority safety | Excellent — AI nodes are read/propose only |
| Human control | Built-in at transitions |
| Cost | Lower — LLM only at draft steps |

**Verdict:** RECOMMENDED (combined with B)

### Option D: n8n-Primary External Orchestration

| Criterion | Score |
|-----------|-------|
| Architectural fit | Moderate — n8n_bridge exists |
| Tenant safety | **RISK** — env-backed, webhook binding complexity |
| Authority safety | Weak — external logic harder to gate |
| Frozen-contract impact | Must not bypass CRM SoT |

**Verdict:** Use n8n as **connector/executor**, not orchestrator

---

## 10. Recommended Architecture

**Single Revenue Workflow Orchestrator (Option B + C)** extending `WorkflowOrchestrator` + `EventBus` + `ApprovalRequest`:

```
[Trigger: demand/contact/event]
   → WorkflowOrchestrator (deterministic steps)
   → [Enrich step: linkedin_enrichment — SERVICE]
   → [Score step: lead_scoring_service — SERVICE, suggest]
   → [Draft step: sales_agents / AIService — AI, propose only]
   → [Gate: ApprovalRequest — HUMAN]
   → [Execute: outreach_service / n8n — SERVICE, side effect]
   → [Audit: AgentActionLog + Activity]
   → [State: CRM services with require_human_mutation_authority]
```

**True AI agents: 0** (reasoning nodes yes; autonomous agents no)

---

## 11. Minimum Viable Revenue Loop

| Aspect | Specification |
|--------|---------------|
| **Entry object** | Existing `Contact` (from prospecting import or QD accept) |
| **Exit state** | `ApprovalRequest` approved → `Activity` scheduled OR n8n handoff logged |
| **AI involvement** | `AGENT_ICP_RESEARCH` + `AGENT_COLD_EMAIL` (draft only) |
| **Deterministic components** | `linkedin_enrichment`, `lead_scoring_service`, `outreach_service.schedule_contact_sequence` |
| **Human gate** | Operator reviews draft in ApprovalRequest before send |
| **Connector** | n8n `send-email` (existing) |
| **Tenant boundary** | TenantContext on all CRM + credential loads |
| **Identity** | HUMAN approves; SERVICE executes post-approval |
| **Audit record** | `AgentActionLog` + `ApprovalRequest` transition + `Activity` |
| **SoTs reused** | Contact, Activity, ApprovalRequest |
| **New persistence** | **NONE** for MVP |
| **Non-goals** | Autonomous send, auto-qualify, auto stage advance, new SoT, seven agents |

---

## 12. Pre-Mortem (10+ Plausible Failures)

| # | CAUSE | EARLY WARNING | ARCHITECTURAL PREVENTION |
|---|-------|---------------|-------------------------|
| 1 | Duplicate business SoT | Second "lead" table or agent state store | Mandate CRM SoT only; agents hold proposals not entities |
| 2 | Uncontrolled AI mutation | Contact status changes without human | Enforce mutation_authority on all write paths; no AI write APIs |
| 3 | Cross-tenant leakage | Contact from org A visible in org B | Regression tests S2.5–S4.5; job envelope org_id |
| 4 | Credential misuse | Agent uses global OpenAI/n8n for all tenants | Org-scoped credentials; document GLOBAL_BY_DESIGN limits |
| 5 | Hallucinated actions | AI claims email sent but wasn't | Separate propose vs execute; audit execute separately |
| 6 | Outreach spam | Approved once, sent many times | Idempotent Activity creation; dedupe keys |
| 7 | Scheduler/retry duplication | Double send on retry | Idempotency keys on n8n trigger |
| 8 | Broken idempotency | Duplicate QD/CO records | MC04.5/MC06.5 idempotency contracts |
| 9 | Stale authority | Send after user demoted | Re-validate membership at execution time |
| 10 | Poor provenance | Cannot trace why email sent | Log prompt hash, approver, model in AgentActionLog |
| 11 | Runaway LLM cost | Unbounded draft generation | Rate limits per org; cost tracking |
| 12 | Orchestration complexity | 7 agents conflicting | Single workflow definition; no competing orchestrators |
| 13 | Connector coupling | n8n down blocks all outreach | Graceful degradation; queue with retry |
| 14 | Weak approval UX | Operators bypass approval | UI enforces ApprovalRequest; no skip API |
| 15 | Conflicting agents | Two drafts for same contact | Workflow instance lock per contact |
| 16 | Incorrect pipeline transitions | AI sets deal to closed-won | A3 frozen human-only; AI cannot call stage API |

---

## 13. Proposed Sprint Sequence

### FOUNDATION (No New Features)

| Sprint | Objective | Stop Condition |
|--------|-----------|----------------|
| REV-ORCH-F1: Legacy Agent Audit | Inventory CrewAI/SDR paths; disable or gate ungoverned mutation | All agent paths documented; ungoverned paths blocked or removed |
| REV-ORCH-F2: AI Provenance Baseline | Add model/prompt/input refs to AgentActionLog for AI drafts | AI draft calls emit provenance |

**Dependencies:** None  
**Frozen contracts affected:** None  
**Migrations:** Provenance fields optional on audit only

### MVP

| Sprint | Objective | Stop Condition |
|--------|-----------|----------------|
| REV-ORCH-MVP: Research-to-Approved-Outreach | Wire Contact → enrich → score → draft → approve → Activity/n8n for one vertical slice | E2E test: one contact through full loop with audit trail |

**Dependencies:** F1, F2  
**Runtime changes:** Workflow step registration only  
**Tests:** E2E approval flow, tenant isolation, no AI mutation

### EXPANSION

| Sprint | Objective |
|--------|-----------|
| REV-ORCH-E1: QD-Triggered Workflow | Marketing handoff auto-starts workflow on QD accept |
| REV-ORCH-E2: Follow-Up Scheduler Authority | Re-validate authority on scheduled Activity execution |
| REV-ORCH-E3: Meeting Inbound Integration | n8n meeting.booked → operator task (no auto-qualify) |

### AUTONOMY (Deferred — Requires Founder Decision)

| Sprint | Objective |
|--------|-----------|
| REV-ORCH-A1: Policy-Gated Auto-Send | Auto-send ONLY for explicit policy + reputation thresholds |
| REV-ORCH-A2: Tenant-Scoped LLM Credentials | Per-org OpenAI keys in ConnectorCredentialRecord |

**Explicit stop:** No autonomy sprint until MVP + expansion stable 30 days

---

## 14. Unknowns Requiring Decision

1. **Calendar integration scope** — native vs n8n-only for BOOK capability
2. **CrewAI agents** — deprecate SDR/Recruiter or bring under WorkflowOrchestrator
3. **Per-tenant OpenAI billing** — required for multi-tenant SaaS or acceptable as platform cost
4. **Auto-qualify policy** — ever allow SERVICE to accept QD without human?
5. **Prospecting provider priority** — Apollo MCP vs scraper vs manual only for MVP
6. **Dual API deprecation timeline** — `revenue_os/main.py` vs `runner_api.py`
7. **Editorial/publishing reads** — deferred; impact on marketing → demand loop

---

## 15. Explicit Non-Goals

- Seven autonomous AI agents
- Parallel lead/opportunity database
- AI-direct mutation of Contact.status or Deal.stage
- Payload-authoritative tenant selection
- Generic agent framework (LangChain/CrewAI as orchestrator)
- Auto-send without ApprovalRequest
- Frozen contract modification (MC04.5, MC06.5, A3, A4, S4.5)
- New connector credentials in repo
- Database migrations in discovery phase
- LLM tool calling against CRM APIs without human gate

---

## 16. Repository Evidence Appendix

### Key Files Read

```
revenue_os/models/contact.py          — Contact, Company, ContactStatus
revenue_os/models/deal.py             — Deal, DealStage
revenue_os/models/activity.py         — Activity, ActivityType
revenue_os/models/approvals.py        — ApprovalRequest
revenue_os/models/integrations.py     — ConnectorCredentialRecord
revenue_os/services/qualified_demand_service.py
revenue_os/services/commercial_outcome_service.py
revenue_os/services/sales_agents.py
revenue_os/services/ai_service.py
revenue_os/services/approvals.py
revenue_os/services/outreach_service.py
revenue_os/services/followups.py
revenue_os/services/lead_prospecting_service.py
revenue_os/services/mutation_authority.py
revenue_os/services/credentials_vault.py
revenue_os/agents/orchestration.py
revenue_os/integrations/n8n.py
revenue_os/scheduler.py
runner_api_routers/crm.py
runner_api_routers/manual_demand.py
runner_api_routers/qualified_demand.py
runner_api_routers/n8n_webhooks.py
runner_api_routers/prospecting.py
runner_api_routers/outreach.py
runner_api_routers/operator_flow.py
docs/integration/mc04_5/
docs/integration/mc06_5/
docs/sales/SALES_REVENUE_CONTRACT.md
```

### Regression Context

- Latest known regression: 859/871 pass (8 failed + 4 errors — pre-existing, not discovery-related)
- Discovery made **zero** code/runtime/migration changes

---

*End of Revenue Agent Orchestration Discovery v1*
