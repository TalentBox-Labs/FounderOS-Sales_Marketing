# M0.5 M1 Worker Contracts

**Sprint:** REV-ORCH M0.5  
**Date:** 2026-08-17  
**M1 workers:** 2 specialized AI workers + 3 deterministic services (not workers)

Do not create seven agents.

---

## M1 specialized AI workers

### 1. Research Worker

| Field | Contract |
|-------|----------|
| **NAME** | `ResearchWorker` |
| **RESPONSIBILITY** | Assemble buying signals and ICP-fit observations for one tenant-scoped Contact |
| **INPUT** | Server-bound `organization_id`, `contact_id`, IdentityContext (non-human worker identity for audit) |
| **OUTPUT** | `ResearchProposal` dict (see output contract) |
| **ALLOWED DATA** | That Contact; related Company; LinkedIn enrichment result for that contact |
| **PROHIBITED DATA** | Connector secrets; other orgs; Deal.stage mutation inputs; credentials |
| **ALLOWED OPERATIONS** | Read tenant-scoped Contact/Company; call `linkedin_enrichment`; call AIService for summary text |
| **PROHIBITED OPERATIONS** | Mutate Contact.status; send; select tenant; select credentials; approve; accept QD/CO |
| **TENANT REQUIREMENT** | TenantContext required; Contact.organization_id must match |
| **IDENTITY REQUIREMENT** | PrincipalKind AGENT or SERVICE; never HUMAN spoof |
| **AUDIT REQUIREMENT** | AgentActionLog `worker_research` with org, contact, success/fail |
| **APPROVAL REQUIREMENT** | Not required for proposal. Activity NOTE (if used) is SERVICE logging, not status mutation |
| **MODEL USAGE** | Optional via AIService; enrichment is deterministic |
| **FAILURE BEHAVIOR** | Return structured failure; no CRM status change; no send |

**Reuse source:** `sales_agents.research_contact` after tenant-scoped lookup.

---

### 2. Personalization Worker (Outreach Draft)

| Field | Contract |
|-------|----------|
| **NAME** | `PersonalizationWorker` |
| **RESPONSIBILITY** | Generate a first-touch email draft from validated contact + optional research context |
| **INPUT** | Tenant-scoped Contact fields; optional ResearchProposal; no secrets |
| **OUTPUT** | `OutreachDraft` dict |
| **ALLOWED DATA** | Name, email, designation, company name/industry/size/funding, recent activity subjects, research summary |
| **PROHIBITED DATA** | Credentials; other contacts; raw Deal pipeline mutations; requested_by |
| **ALLOWED OPERATIONS** | Call AIService to generate body/subject; return proposal |
| **PROHIBITED OPERATIONS** | File ApprovalRequest itself if policy prefers orchestrator filing; **never** `trigger_workflow`; never send |
| **TENANT REQUIREMENT** | TenantContext required |
| **IDENTITY REQUIREMENT** | AGENT/SERVICE worker identity |
| **AUDIT REQUIREMENT** | AgentActionLog `worker_personalize` |
| **APPROVAL REQUIREMENT** | Orchestrator files ApprovalRequest `send_outreach_email` from validated draft. Human must approve before send |
| **MODEL USAGE** | AIService (platform OpenAI) |
| **FAILURE BEHAVIOR** | No ApprovalRequest filed; no send; audit failed |

**Reuse source:** `sales_agents.draft_cold_email` body generation. **M1 should split** “generate draft” (worker) from “file ApprovalRequest” (orchestrator/domain). Current code files approval inside the module — REFACTOR.

---

## M1 deterministic components (not workers)

| Name | Role |
|------|------|
| `linkedin_enrichment` | DETERMINISTIC_SERVICE — provider fetch |
| `lead_scoring_service.score_contact` / `LeadScorer` | DETERMINISTIC_SERVICE — score/recommend; must not apply Contact.status |
| Outreach executor | `approvals.EXECUTORS["send_outreach_email"]` → n8n |

---

## Explicitly not M1 workers

- Follow-Up Worker
- Objection Worker
- LinkedIn Opener Worker
- Qualification Worker
- Pipeline Worker
- Booking Worker

---

*End of M0.5 M1 Worker Contracts*
