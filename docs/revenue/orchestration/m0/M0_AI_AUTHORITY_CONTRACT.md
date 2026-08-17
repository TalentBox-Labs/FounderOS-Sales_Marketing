# M0 AI Authority Contract

**Sprint:** REV-ORCH M0  
**Date:** 2026-08-17  
**Status:** Conceptual freeze for M1 (not a frozen baseline)

---

## Principle

**AI MAY PROPOSE → FOUNDER OS POLICY/AUTHORITY DECIDES → DOMAIN SERVICES MUTATE → AUDIT RECORDS WHO/WHAT/WHY**

---

## AI MAY

| Capability | Example | Repository path |
|------------|---------|-----------------|
| Read tenant-authorized context | Contact CRM context for draft | `sales_agents._build_contact_context` |
| Summarize | ICP research summary | `sales_agents.research_contact` |
| Research | LinkedIn enrichment narrative | `linkedin_enrichment` + `sales_agents` |
| Score/recommend | Lead score suggestion | `lead_scoring_service.score_contact` |
| Propose content | Cold email body | `AIService.generate_cold_email` |
| Propose next action | ApprovalRequest filing | `approvals.request_approval` |
| Generate structured draft output | JSON in ApprovalRequest.payload | `draft_cold_email` |

---

## AI MUST NOT

| Prohibition | Enforcement | Evidence |
|-------------|-------------|----------|
| Mutate `Contact.status` directly | `require_human_mutation_authority` (A4) | `mutation_authority.py`, `contact_status_service.py` |
| Mutate `Deal.stage` directly | A3 human gate | `deal` routes, frozen tests |
| Accept/reject QualifiedDemand | MC04.5 human gate | `qualified_demand_service.py` |
| Accept/reject CommercialOutcome | MC06.5 human gate | `commercial_outcome_service.py` |
| Send outbound messages directly | ApprovalRequest executor only | `approvals.py` `_execute_send_outreach_email` |
| Choose connector credentials | S4.5 org-scoped vault | `credentials_vault.py` |
| Choose organization/tenant authority | Server-derived TenantContext | `tenant_context.py` |
| Spoof `requested_by` | Server-bound identity | S1.5 frozen |
| Invoke arbitrary domain tools | **Not implemented** | No tool calling in repo |
| Create SoT outside approved services | CRM services only | Model layer |
| Bypass ApprovalRequest for outbound | sales_agents file ApprovalRequest | Module docstring + implementation |

---

## Canonical Pattern

```
AIService / sales_agents (AI proposal)
  → structured proposal dict / ApprovalRequest.payload
  → Founder OS validation (contact exists, email present, action_type registered)
  → ApprovalRequest (when external or business mutation follows)
  → human decide() via /api/v1/approvals
  → EXECUTORS[action_type] (deterministic)
  → AgentActionLog + execution_result
```

---

## Identity Types

| Identity | AI proposal | Approval decision | Domain mutation |
|----------|-------------|-------------------|-----------------|
| HUMAN | Allowed | **Required** for protected mutations | Allowed (with role) |
| SERVICE | Allowed (via sales_agents requested_by) | No | Policy-dependent |
| AGENT | Allowed (requested_by=agent name) | No | **Prohibited** for A3/A4/QD/CO |
| AI | Same as AGENT for audit | **Prohibited** | **Prohibited** |

Evidence: `is_human_approver()` excludes `crewai`, agent names; MC06.5 freeze tests block agent/AI mutation.

---

## M0 Exception: research_contact Activity Write

`research_contact` writes an Activity NOTE without human approval. This is **deterministic enrichment logging**, not status mutation. M1 should:
- Require TenantContext on contact lookup
- Treat as SERVICE identity audit event

---

*End of M0 AI Authority Contract*
