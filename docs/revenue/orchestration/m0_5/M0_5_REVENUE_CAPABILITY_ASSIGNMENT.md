# M0.5 Revenue Capability Assignment

**Sprint:** REV-ORCH M0.5  
**Date:** 2026-08-17

---

## Method

Each of the seven conceptual capabilities is assigned **one primary** taxonomy class, verified against repository implementation (not the external seven-agent inspiration).

---

| Capability | Discovery classification | Repository evidence | Primary assignment | Notes |
|------------|-------------------------|---------------------|--------------------|-------|
| **FIND** | EXISTING_CAPABILITY | `lead_prospecting_service`, `prospecting.py`, `manual_demand.py`, MC04 register | **EXISTING_DOMAIN_CAPABILITY** + **DETERMINISTIC_SERVICE** | No specialized AI worker for M1. Import/register already exist. |
| **RESEARCH** | HYBRID | `linkedin_enrichment`, `research_contact` | **HYBRID**: DETERMINISTIC_SERVICE (enrich) + **SPECIALIZED_AI_WORKER** (narrative/signals assembly) | M1 Research Worker. Enrichment is not LLM-required. |
| **PERSONALIZE** | AI_ASSISTED_SERVICE | `draft_cold_email`, `AIService.generate_cold_email` | **SPECIALIZED_AI_WORKER** | M1 Personalization Worker. Proposal only. |
| **OUTREACH** | HYBRID | `ApprovalRequest`, `approvals._execute_send_outreach_email`, `outreach_service` | **WORKFLOW_STATE_MACHINE** + HUMAN_ACTION + **CONNECTOR_EXECUTION** | Not an agent. Orchestrator + approval + n8n. |
| **FOLLOW-UP** | WORKFLOW_STATE_MACHINE + SCHEDULED_WORKFLOW | `followups.py`, Activity schedule, `build_followup_sequence` | **WORKFLOW_STATE_MACHINE** + optional future **SPECIALIZED_AI_WORKER** | Current `build_followup_sequence` mutates sequence SoT — not authorized as worker write. |
| **BOOK** | HUMAN_ACTION + n8n signal | inbound `meeting.booked`; no native calendar | **HUMAN_ACTION** + **CONNECTOR_EXECUTION** (inbound) | No booking worker. No auto-qualify. |
| **CLOSE / PIPELINE** | EXISTING_CAPABILITY | A3 Deal.stage, A4 Contact.status, MC06 CommercialOutcome | **EXISTING_DOMAIN_CAPABILITY** + **HUMAN_ACTION** | No pipeline-mutation worker. Recommendation-only possible later. |

---

## Explicit non-assignments

| Not created | Why |
|-------------|-----|
| Lead Finder Agent | FIND is existing deterministic import/register |
| Appointment Setter Agent | BOOK is human + inbound signal |
| Sales Manager Agent | CLOSE is frozen human-gated domain |
| Outreach Agent that sends | Send is connector after human approval |

---

## M1 slice mapping

```
FIND          — reuse existing Contact (already found/imported)
RESEARCH      — Research Worker + linkedin_enrichment
PERSONALIZE   — Personalization Worker
OUTREACH      — WorkflowOrchestrator + ApprovalRequest + n8n
FOLLOW-UP     — out of M1
BOOK          — out of M1
CLOSE         — out of M1 (frozen)
```

---

*End of M0.5 Revenue Capability Assignment*
