# M0.5 Specialized Agent Inventory

**Sprint:** REV-ORCH M0.5  
**Date:** 2026-08-17  
**Status:** Architecture freeze input (not a product feature)

---

## Principle applied

**AGENT ≠ AUTHORITY.** Inventory classifies cognitive/reasoning modules separately from business mutation authority.

---

## Inventory

| Component | File / symbol | Current responsibility | Inputs | Outputs | Model | Domain mutation | Connector | ApprovalRequest | TenantContext | Identity | Audit | Production reachability | Suitability | Classification |
|-----------|---------------|------------------------|--------|---------|-------|-----------------|-----------|-----------------|---------------|----------|-------|-------------------------|-------------|----------------|
| ICP Research | `sales_agents.research_contact` | LinkedIn enrichment + ICP fit summary | `contact_id` | dict signals + icp_fit | Enrichment APIs; LLM not primary | Activity NOTE write | Proxycurl via `linkedin_enrichment` | No | **No** (ID-only) | None | Activity NOTE | `POST /api/v1/agents/sales/{id}/research` on runner_api | M1 research worker after tenant fix | **REFACTOR_FOR_M1** |
| Cold Email | `sales_agents.draft_cold_email` | Draft first-touch email | `contact_id` | body + approval_id | `AIService.generate_cold_email` | Activity NOTE | None (draft only) | **Yes** `send_outreach_email` | **No** | `requested_by=cold_email_agent` | ApprovalRequest + NOTE | runner_api sales route | M1 personalization worker after tenant fix | **REFACTOR_FOR_M1** |
| LinkedIn Opener | `sales_agents.draft_linkedin_opener` | Draft connection note + DM | `contact_id` | opener dict + approval_id | `AIService.generate_linkedin_opener` | Activity NOTE | None | **Yes** `send_linkedin_message` (manual delivery) | **No** | `linkedin_opener_agent` | ApprovalRequest | runner_api | Post-M1 channel | **FUTURE_WORKER** |
| Follow-Up Sequence | `sales_agents.build_followup_sequence` | Build 5–7 step sequence | `contact_id` | `sequence_id` + steps | `AIService.generate_followup_sequence` | **Creates OutreachSequence + SequenceStep** | None | **No** | **No** | None | Activity NOTE | runner_api | Must become proposal-only before reuse | **FUTURE_WORKER** (unsafe as autonomous writer) |
| Objection Handler | `sales_agents.handle_latest_reply` | Classify inbound + draft reply | `contact_id` | category + draft + approval_id | `AIService.classify_and_draft_reply` | Activity NOTE | None | **Yes** `send_reply_email` | **No** | `objection_handler_agent` | ApprovalRequest | runner_api | Post-M1 | **FUTURE_WORKER** |
| AIService | `revenue_os/services/ai_service.py` | LLM text generation | prompt strings | text / JSON-ish dict | OpenAI env key | **None** | OpenAI HTTP | N/A | N/A | N/A | None | Internal | Platform model access layer | **REUSE_AS_DETERMINISTIC_SERVICE** (platform LLM adapter, not a worker) |
| AgentCoordinator | `orchestration.py` | Registry, messages, touch | agent name | registry dict | None | Registry persistence | None | No | No | API key | Optional DB | runner_api `/registry` | Subordinate metadata | **REUSE_AS_DETERMINISTIC_SERVICE** |
| WorkflowOrchestrator | `orchestration.py` | In-memory workflow dispatch | workflow_id, context dict | WorkflowExecution | None | Stub `_execute_agent` | None | No | No | API key | In-memory | runner_api `/workflows/*/execute` | Canonical orchestrator (stub today) | **REUSE_AS_DETERMINISTIC_SERVICE** |
| HermesPlanner | `hermes_planner.py` | Goal → plan / propose outreach | goals, contacts | plans; ApprovalRequest for outreach | Optional LLM | Propose via approval | Indirect | Yes (outreach) | Partial | `hermes` | AgentActionLog | runner_api hermes + heartbeat | Subordinate planner | **REFACTOR_FOR_M1** (must not become second orchestrator) |
| GoToMarketOrchestrator | `go_to_market_orchestrator.py` | Marketing GTM channel run | brand/topic/channels | file audit + n8n | Optional | Marketing artifacts | n8n | No | No | API key | File dir | runner_api `/api/v1/orchestration` | **Not revenue CRM** | **DUPLICATE** (marketing adapter, not revenue worker) |
| n8n_bridge | `integrations/n8n.py` `trigger_workflow` | Outbound webhook executor | webhook_id, payload | HTTP result | None | External send | n8n env | Used by approval executor | Partial (payload IDs) | `platform` | AgentActionLog `n8n_outbound` | Post-approval | Connector executor | **REUSE_AS_DETERMINISTIC_SERVICE** |
| CrewAI SDR | `agents/sdr_agent.py` | Score + outreach sequence JSON | company/prospect strings | JSON dict/list | CrewAI + OpenAI/Gemini | **None** | LLM only | **No** | **No** | None | No | HTTP unmounted; Celery `score_lead_background` | Do not integrate | **QUARANTINED** (HTTP) / **LEGACY** (Celery) |
| CrewAI Recruiter | `agents/recruiter_agent.py` | Match/screen resume JSON | candidate/job strings | JSON | CrewAI | **None** | LLM only | No | No | None | No | Unmounted | Out of revenue scope | **QUARANTINED** |
| EventBus | `automation/events.py` | Pub/sub | event payloads | subscriber calls | None | Indirect | Varies | Varies | No | None | Partial | Production | Infrastructure | **REUSE_AS_DETERMINISTIC_SERVICE** |
| HeartbeatScheduler | `scheduler.py` | Interval jobs | none | scores/events | None | lead_score write (suggest path) | None | No | **No** | `heartbeat` | AgentActionLog | runner_api startup | Scheduler infra | **REUSE_AS_DETERMINISTIC_SERVICE** |
| DecisionManager / TaskQueue | `agents/execution.py` | In-memory agent tasks | API payloads | dicts | None | No CRM | None | Parallel to ApprovalRequest | No | API key | Safeguard audit | runner_api `/tasks` `/decisions` | Duplicate authority surface | **DEPRECATED** (do not use for M1) |
| Editorial CrewAI (`src/*_crew.py`) | generation/editor/qa | Editorial pipeline | week files | markdown | CrewAI | Editorial files | None | Editorial human gate | N/A | N/A | Editorial | Marketing pipeline | Not revenue | **DEAD** (revenue scope) |

---

## Non-overlapping responsibility (target)

| Cognitive role | Owner |
|----------------|-------|
| Research reasoning | Research Worker (from `research_contact`) |
| Message generation | Personalization Worker (from `draft_cold_email`) |
| Scoring math | `LeadScorer` / `lead_scoring_service` |
| Workflow sequencing | `WorkflowOrchestrator` |
| External send | n8n via ApprovalRequest executor |
| Business mutation | Domain services + human authority |

---

## Unsafe findings (must not be treated as specialized workers as-is)

1. **`build_followup_sequence`** persists `OutreachSequence` without ApprovalRequest — worker must become proposal-only before FUTURE reuse.
2. **All `sales_agents` functions** load Contact by ID without TenantContext.
3. **CrewAI SDR outreach-sequence** returns drafts without ApprovalRequest (HTTP quarantined).

---

*End of M0.5 Specialized Agent Inventory*
