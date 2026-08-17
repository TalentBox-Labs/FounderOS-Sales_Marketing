# M0 Canonical Orchestrator Decision

**Sprint:** REV-ORCH M0  
**Date:** 2026-08-17  
**Decision status:** APPROVED for M1 planning

---

## Decision

**Canonical Revenue Orchestrator:** `WorkflowOrchestrator` in `revenue_os/agents/orchestration.py`

**Canonical orchestration entry (M1):** `runner_api_routers/agents.py` — workflow + sales agent routes on `runner_api:app`, extended to require `TenantContext` in M1.

**Rationale:** Repository evidence shows `WorkflowOrchestrator` is the designated multi-step workflow abstraction, seeded alongside platform agents at startup (`seed_platform_agents()` in `runner_api.py`), and exposed via production API. No second orchestrator should be introduced.

---

## Required Canonical Contract (M1 target)

```
IdentityContext (server-derived)
  → TenantContext (server-derived organization scope)
  → authority/policy evaluation (mutation_authority, is_human_approver)
  → deterministic workflow step OR AI proposal step (sales_agents / AIService)
  → ApprovalRequest (when external side effect or privileged mutation follows)
  → domain service execution (CRM services, outreach_service, n8n bridge)
  → audit/provenance (AgentActionLog, ApprovalRequest transitions)
```

---

## Component Classification

| Component | Classification | Role |
|-----------|----------------|------|
| `WorkflowOrchestrator` | **CANONICAL** | Future revenue workflow definition and step dispatch |
| `AgentCoordinator` | **SUBORDINATE** | Agent registry, heartbeat metadata, inter-agent messaging |
| `EventBus` | **SUBORDINATE** | Decoupled event triggers; must not bypass authority gates |
| `HeartbeatScheduler` | **SUBORDINATE** | Scheduled deterministic jobs; must carry org envelope in M1+ |
| `HermesPlanner` | **SUBORDINATE** | Goal planning; already uses ApprovalRequest for outreach |
| `GoToMarketOrchestrator` | **ADAPTER** | Marketing/GTM scope — not revenue CRM orchestrator |
| `sales_agents` (5 modules) | **SUBORDINATE** | AI reasoning nodes; invoke via orchestrator/workflow steps |
| `AIService` | **SUBORDINATE** | LLM text generation; propose-only |
| `ApprovalRequest` / `approvals.py` | **SUBORDINATE** | Human gate + execution dispatch |
| `n8n_bridge` / `integrations/n8n.py` | **ADAPTER** | Connector executor, not orchestrator |
| CrewAI `sdr_agent` / `recruiter_agent` | **LEGACY** | Quarantined from legacy API; not canonical |
| `revenue_os/api/v1/agents.py` | **DEPRECATED** | 410 Gone (M0 quarantine) |
| `revenue_os/main.py` v1 routers | **LEGACY_COMPATIBILITY** | Not production entry |
| CrewAI editorial crews (`src/*_crew.py`) | **DEAD** (revenue scope) | Editorial pipeline only |
| `DecisionManager` / `TaskQueue` | **LEGACY** | In-memory agent task/decision — not wired to CRM authority |
| `WorkflowOrchestrator._execute_agent` | **UNKNOWN → STUB** | Placeholder; M1 must wire to sales_agents/services |

---

## Why Not Create a New Orchestrator

1. `WorkflowOrchestrator` already registered in production startup.
2. `AgentCoordinator` already lists revenue-relevant agents (5 sales draft agents).
3. `runner_api_routers/agents.py` already exposes workflow CRUD + sales agent endpoints.
4. Introducing a parallel orchestrator would violate discovery recommendation and increase cross-agent conflict risk.

---

## M0 Gap: Stub Agent Execution

Current `_execute_agent()` returns placeholder dict — it does **not** invoke `sales_agents` or domain services. M1 must wire workflow steps to real capabilities without bypassing ApprovalRequest.

Evidence:

```312:321:revenue_os/agents/orchestration.py
    def _execute_agent(cls, agent_name: str, context: dict[str, Any]) -> dict[str, Any]:
        """Execute a single agent."""
        # Placeholder for actual agent execution
        # In production, this would call the actual agent/crew
        return {
            "decision": f"action_by_{agent_name}",
            ...
        }
```

---

## Canonical vs Parallel Paths

| Path | Status |
|------|--------|
| `POST /api/v1/agents/workflows/{id}/execute` | Canonical target (stub today) |
| `POST /api/v1/agents/sales/{contact_id}/cold-email` | Subordinate direct invoke — M1 should route through workflow or add TenantContext |
| Hermes goal check → ApprovalRequest | Subordinate — compliant pattern |
| Heartbeat lead scoring | Subordinate — deterministic, no send |

---

*End of M0 Canonical Orchestrator Decision*
