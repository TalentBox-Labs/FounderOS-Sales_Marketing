# M0.5 Agent Context Boundaries

**Sprint:** REV-ORCH M0.5  
**Date:** 2026-08-17

---

## Rule

Each worker receives **only** the context required for its cognitive job.

Current `_build_contact_context` in `sales_agents.py` is a reasonable starting set for personalization; it must be **tenant-filtered** and must not grow into unrestricted DB access.

---

## Research Worker — minimum context

| Include | Exclude |
|---------|---------|
| contact_id, org_id (server) | Connector credentials / API keys |
| linkedin_url | Unrelated Deal records |
| company name, industry, size, funding (from enrichment or Company) | Other tenants |
| person enrichment profile used for signals | ApprovalRequest queue |
| | Human identity tokens |

---

## Personalization Worker — minimum context

| Include | Exclude |
|---------|---------|
| first_name, name, email, designation | Raw credential vault |
| company_name, industry, employee_count, funding_stage | Full deal pipeline dump |
| recent_activity subjects (≤3) | Other contacts |
| optional research summary string | Approval authority / decided_by |
| | Full LinkedIn profile dump unless needed |

Do **not** pass unrestricted Session or “query anything” tools.

---

## Follow-Up Worker (future) — minimum context

| Include | Exclude |
|---------|---------|
| Bounded conversation: last N inbound/outbound Activity bodies for that contact | Broad CRM search |
| last send date / sequence position | Org-wide followups list |
| prior OutreachDraft if any | Credentials |

---

## Objection Worker (future) — minimum context

| Include | Exclude |
|---------|---------|
| latest inbound email body | All historical deals |
| contact identity fields as personalization | Cross-contact threads |

---

## Orchestrator context (not a worker)

May hold workflow_id, step, organization_id, actor ref, approval_id, policy_version.

Must **not** pass the full orchestrator context blob into the LLM prompt.

---

## Benefits (why this is frozen)

Tenant safety, prompt quality, token cost, observability, reproducibility, model portability.

---

*End of M0.5 Agent Context Boundaries*
