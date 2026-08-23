# M0 Orchestration Entrypoint Inventory

**Sprint:** REV-ORCH M0  
**Date:** 2026-08-17  
**Purpose:** Complete inventory of paths capable of initiating or coordinating revenue-related work.

---

## Summary

| Category | Count | Canonical? |
|----------|-------|------------|
| Revenue orchestration abstractions | 6 | 1 canonical (WorkflowOrchestrator) |
| AI proposal services | 6 | Subordinate to ApprovalRequest |
| Legacy CrewAI paths | 3 | Quarantined / not on runner_api |
| Runner API revenue routes | 12+ routers | Canonical production surface |
| Legacy revenue_os/main.py | 1 app | LEGACY_COMPATIBILITY |
| Background schedulers | 2 | Subordinate (HeartbeatScheduler, Celery) |

---

## 1. Orchestration Abstractions

| Component | Path | Symbol | Invocation | Sync/Async | Tenant | Identity | Mutation | Approval | Audit | Reachability | Bypasses Canonical? |
|-----------|------|--------|------------|------------|--------|----------|----------|----------|-------|--------------|---------------------|
| WorkflowOrchestrator | `revenue_os/agents/orchestration.py` | `WorkflowOrchestrator` | `runner_api_routers/agents.py` POST `/workflows/*/execute` | Sync | **None today** | API key only | Stub only (`_execute_agent` placeholder) | No | In-memory only | Production (runner_api) | N/A — is canonical target |
| AgentCoordinator | Same | `AgentCoordinator` | Startup `seed_platform_agents()`, registry routes | Sync | None | API key | Registry only | No | Optional DB write-through | Production | No — registry/metadata |
| EventBus | `revenue_os/automation/events.py` | `emit_*` | Heartbeat, deal risk, CRM events | Sync | **None** | Event payload | Indirect via subscribers | Varies | Partial | Production | Yes — subscribers ungated |
| HeartbeatScheduler | `revenue_os/scheduler.py` | `HeartbeatScheduler` | FastAPI startup asyncio loop | Scheduled | **None** — global query | `heartbeat` actor | Lead score suggest, events | No | `AgentActionLog` | Production (runner_api) | Yes — no TenantContext |
| HermesPlanner | `revenue_os/services/hermes_planner.py` | goal planning | `runner_api_routers/hermes.py`, heartbeat job | Sync/scheduled | Partial | `hermes` | Proposes via ApprovalRequest | Yes (outreach) | Yes | Production | Partial bypass |
| GoToMarketOrchestrator | `revenue_os/services/go_to_market_orchestrator.py` | `run_orchestration` | `runner_api_routers/orchestration.py` | Sync | None | API key | Marketing channels via n8n | No | File audit dir | Production | Yes — marketing not revenue CRM |

---

## 2. AI / Proposal Services

| Component | Path | Symbol | Invocation | Mutation | Approval | Reachability |
|-----------|------|--------|------------|----------|----------|--------------|
| AIService | `revenue_os/services/ai_service.py` | `_chat`, `generate_*` | sales_agents, legacy callers | **None** — text only | N/A | Internal |
| sales_agents (5) | `revenue_os/services/sales_agents.py` | `research_contact`, `draft_*` | `runner_api_routers/agents.py` `/sales/{id}/*` | Activity NOTE on research | Draft agents → ApprovalRequest | Production |
| CrewAI sdr_agent | `revenue_os/agents/sdr_agent.py` | `score_and_enrich_lead`, `generate_outreach_sequence` | Legacy API (quarantined), Celery task | **None** | **No** | Legacy quarantined; Celery worker |
| CrewAI recruiter_agent | `revenue_os/agents/recruiter_agent.py` | `match_candidate_to_job`, `screen_resume` | Legacy API (quarantined) | **None** | No | Legacy quarantined |

---

## 3. Runner API Revenue Routes (Canonical Production — `runner_api:app`)

| Router | Prefix | Revenue relevance | TenantContext | Auth |
|--------|--------|-------------------|---------------|------|
| `crm.py` | `/api/crm` | Contact/Deal/Company/Activity SoT | **Yes** | Session + org cookie |
| `manual_demand.py` | `/api/manual-demand` | Demand registration (MDG1.5) | **Yes** | Human operator |
| `qualified_demand.py` | `/api/qualified-demand` | MC04.5 handoff | **Yes** | Human gate |
| `commercial_outcome.py` | `/api/commercial-outcome` | MC06.5 handoff | **Yes** | Human gate |
| `approvals.py` | `/api/v1/approvals` | Human approval queue | **No org field** | API key |
| `agents.py` | `/api/v1/agents` | Registry, workflows, sales agents | **Partial gap** | API key |
| `outreach.py` | `/api/outreach` | Sequence scheduling | Partial | API key |
| `prospecting.py` | `/api/prospecting` | Lead import | Partial | API key |
| `n8n_webhooks.py` | `/api/webhooks/n8n` | Inbound events (S4.5) | **Yes** — binding | Webhook secret |
| `cockpit.py` | `/cockpit` | Read model (UI2.5) | **Yes** | Session |
| `operator_flow.py` | `/operator-flow` | Operator UI (OF1.5) | **Yes** | Session |
| `integrations.py` | `/api/integrations` | Connector credentials (S4.5) | **Yes** | Session |

---

## 4. Legacy API Surface (`revenue_os/main.py`)

| Router | Prefix | Status | Notes |
|--------|--------|--------|-------|
| `revenue_os/api/v1/agents.py` | `/api/v1/agents` | **QUARANTINED (410)** | CrewAI routes blocked M0 |
| `revenue_os/api/v1/contacts.py` | `/api/v1/contacts` | LEGACY | No TenantContext guards |
| `revenue_os/api/v1/deals.py` | `/api/v1/deals` | LEGACY | No TenantContext guards |
| `revenue_os/api/v1/orchestration.py` | `/api/v1/orchestration` | LEGACY | GTM marketing orchestrator |

**Production Dockerfile CMD:** `uvicorn runner_api:app` — legacy main.py **not** production entry.

---

## 5. Background Jobs

| Job | Path | Trigger | TenantContext | Authority revalidation |
|-----|------|---------|---------------|------------------------|
| Heartbeat lead scoring | `scheduler.py` `job_score_new_leads` | Interval | **No** | N/A — suggest only |
| Heartbeat deal risk | `scheduler.py` `job_check_deals_at_risk` | Interval | **No** | N/A — read/emit |
| Celery `score_lead_background` | `revenue_os/tasks/agents.py` | Worker queue | **No** | N/A — propose only |
| Celery outreach tasks | `revenue_os/tasks/outreach.py` | Worker queue | **Unknown** | **Gap** |

---

## 6. Webhooks & Connectors

| Path | Symbol | Tenant binding | Side effects |
|------|--------|----------------|--------------|
| `n8n_webhooks.py` | inbound handlers | S4.5 org binding | Recommendations only |
| `n8n_bridge` / `integrations/n8n.py` | `trigger_workflow` | Payload carries contact_id | Outbound send (post-approval) |
| `credentials_vault.py` | `load_credentials` | S4.5 org-scoped | Credential access |

---

## 7. Tests / Fixtures Executing Agent Paths

| Test file | Path executed | Classification |
|-----------|---------------|----------------|
| `tests/conftest.py` | CrewAI mock | TEST_ONLY |
| `tests/test_pipeline_runner.py` | CrewAI QA | TEST_ONLY — editorial |
| No tests | sdr_agent production routes | N/A |

---

## 8. Parallel Orchestration Assessment

| Path | Can execute without WorkflowOrchestrator? | Risk |
|------|-------------------------------------------|------|
| sales_agents direct via agents router | **Yes** | MEDIUM — missing TenantContext on contact_id |
| Hermes heartbeat | **Yes** | MEDIUM — proposes with ApprovalRequest |
| Heartbeat lead scoring | **Yes** | LOW — no status mutation |
| GoToMarketOrchestrator | **Yes** | LOW — marketing scope |
| CrewAI legacy (quarantined) | **No** — 410 | CONTAINED |
| EventBus subscribers | **Yes** | MEDIUM — depends on subscriber |

---

*End of M0 Orchestration Entrypoint Inventory*
