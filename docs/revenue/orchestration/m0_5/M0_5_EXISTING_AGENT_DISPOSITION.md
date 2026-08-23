# M0.5 Existing Agent Disposition

**Sprint:** REV-ORCH M0.5  
**Date:** 2026-08-17

---

## Critical question

**Can existing specialized modules become bounded proposal-only workers rather than autonomous agents?**

**YES** for ICP research, cold email, LinkedIn opener, objection handler — they already draft and (except research) file ApprovalRequest; they do not send.

**NOT YET** for `build_followup_sequence` — it persists `OutreachSequence` without ApprovalRequest.

**NO** for CrewAI SDR/recruiter as canonical workers — quarantined/legacy, no TenantContext, outreach-sequence bypasses ApprovalRequest.

Do not delete code in M0.5.

---

## sales_agents.py (five functions)

| Function | Constant | Exactly one disposition | Why |
|----------|----------|-------------------------|-----|
| `research_contact` | `AGENT_ICP_RESEARCH` | **M1_REFACTOR** | Right cognitive job. Must add TenantContext; treat Activity NOTE as service log; emit AgentActionLog; stop ID-only lookup. |
| `draft_cold_email` | `AGENT_COLD_EMAIL` | **M1_REFACTOR** | Right cognitive job. Split generate vs ApprovalRequest filing (orchestrator files). TenantContext. Keep proposal-only send path. |
| `draft_linkedin_opener` | `AGENT_LINKEDIN_OPENER` | **FUTURE_REUSE** | Same pattern; not M1 channel. Tenant fix when reused. |
| `build_followup_sequence` | `AGENT_FOLLOWUP_SEQUENCE` | **FUTURE_REUSE** | Must stop creating OutreachSequence as a worker. Convert to FollowUpProposal first. |
| `handle_latest_reply` | `AGENT_OBJECTION_HANDLER` | **FUTURE_REUSE** | Already ApprovalRequest for reply; needs tenant; not M1. |

No sales_agents module is **M1_REUSE unchanged** — all lack TenantContext.

---

## Other modules

| Module | Disposition | Why |
|--------|-------------|-----|
| `AIService` | **M1_REUSE** | Propose-only LLM wrapper. No CRM mutation. |
| `linkedin_enrichment` | **M1_REUSE** | Deterministic enrich. |
| `lead_scoring_service` | **M1_REUSE** | Deterministic score; must not apply A4 status. |
| `approvals.py` | **M1_REUSE** | Human gate + executors. |
| `WorkflowOrchestrator` | **M1_REFACTOR** | Stub `_execute_agent`; wire steps or use orchestrator facade over existing routes. |
| `AgentCoordinator` | **LEGACY** as authority; **M1_REUSE** as registry only | Messages must not confer authority. |
| CrewAI `sdr_agent` | **QUARANTINE** (HTTP) / **DEPRECATE** (Celery enqueue for M1) | No ApprovalRequest on sequence; no tenant. |
| CrewAI `recruiter_agent` | **QUARANTINE** | Not revenue. |
| `revenue_os/api/v1/agents.py` | **QUARANTINE** | Unmounted M0. |
| `DecisionManager` / `TaskQueue` | **DEPRECATE** | Parallel in-memory authority; not ApprovalRequest. |
| HermesPlanner | **FUTURE_REUSE** | Subordinate planner; not M1 orchestrator. |
| GoToMarketOrchestrator | **LEGACY** for revenue | Marketing only. |

---

## Disposition counts

- M1_REUSE: AIService, linkedin_enrichment, lead_scoring_service, approvals
- M1_REFACTOR: research_contact, draft_cold_email, WorkflowOrchestrator
- FUTURE_REUSE: LinkedIn, follow-up, objection, Hermes
- QUARANTINE/DEPRECATE/LEGACY: CrewAI pair, DecisionManager, GTM-as-revenue

---

*End of M0.5 Existing Agent Disposition*
