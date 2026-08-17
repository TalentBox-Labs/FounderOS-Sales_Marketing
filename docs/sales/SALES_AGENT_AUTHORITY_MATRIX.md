# Sales OS — Agent Authority Matrix

**Sprint:** SALES A1  
**Date:** 2026-08-13  
**Status:** DEFINED (governance)  
**ADR:** [Architecture_ADR_004.md](../architecture/Architecture_ADR_004.md)

Resolves A0: **Agent Governance Boundary: PARTIAL** → **DEFINED**.

Classifications: **AUTONOMOUS_ALLOWED** · **HUMAN_APPROVAL_REQUIRED** · **HUMAN_ONLY** · **PROHIBITED**

Default: high-impact external or commercial actions → **HUMAN_APPROVAL_REQUIRED** unless noted.

---

## Matrix

| Operation | Classification | Rationale / current evidence |
|-----------|----------------|------------------------------|
| Lead research (read public info, RAG) | **AUTONOMOUS_ALLOWED** | Agent assists; no mutation |
| Lead enrichment (Proxycurl call) | **HUMAN_APPROVAL_REQUIRED** | External API + PII; config-gated |
| Lead scoring (compute score) | **AUTONOMOUS_ALLOWED** | Recommendation only if **no auto status write** |
| Lead scoring → auto Contact.status change | **HUMAN_APPROVAL_REQUIRED** | **Current gap:** `LeadScorer.update_contact_status` mutates without approval — must migrate |
| Qualification recommendation | **AUTONOMOUS_ALLOWED** | Draft tier/suggestion |
| Qualification decision (SQL) | **HUMAN_ONLY** | Business decision |
| Draft outreach email / LI opener / sequence | **AUTONOMOUS_ALLOWED** | `sales_agents.py` generate paths |
| Send outreach email | **HUMAN_APPROVAL_REQUIRED** | `approvals.py` → n8n today |
| Send LinkedIn message | **HUMAN_APPROVAL_REQUIRED** | Approval executor |
| CRM Contact create | **HUMAN_APPROVAL_REQUIRED** | API key = operator; future explicit gate for agent-initiated |
| CRM Contact modify (fields) | **HUMAN_APPROVAL_REQUIRED** | PII mutation |
| Pipeline stage change | **HUMAN_ONLY** | Core sales accountability |
| Deal create | **HUMAN_APPROVAL_REQUIRED** | Planner path uses approvals |
| Deal value modification | **HUMAN_ONLY** | Commercial impact |
| Forecast modification | **HUMAN_ONLY** | Revenue OS domain |
| Meeting scheduling (calendar write) | **HUMAN_APPROVAL_REQUIRED** | External side effect |
| Follow-up creation | **AUTONOMOUS_ALLOWED** | Task suggest OK; auto-create → **HUMAN_APPROVAL_REQUIRED** |
| Task creation | **HUMAN_APPROVAL_REQUIRED** | If agent-initiated |
| Contact deletion | **HUMAN_ONLY** | Destructive |
| Deal deletion | **HUMAN_ONLY** | Destructive |
| External messaging (any channel) | **HUMAN_APPROVAL_REQUIRED** | Default |
| Commercial commitment | **HUMAN_ONLY** | Contract/pricing |
| Pricing / discount changes | **HUMAN_ONLY** | **PROHIBITED** for agents |
| Enable revenue-impacting automation | **HUMAN_ONLY** | Architecture v2.2 gate |
| Autonomous bulk prospecting execute | **PROHIBITED** | No silent mass outreach |

---

## Founder OS principle

Automate **preparation and orchestration**; preserve **accountability** for mutations, external sends, and commercial outcomes.

---

## Current gaps (not fixed in A1)

| Gap | Target classification | Migration |
|-----|----------------------|-----------|
| LeadScorer silent status promotion | HUMAN_APPROVAL_REQUIRED | REQUIRES_FUTURE_MIGRATION |
| API-key CRM writes without actor audit | HUMAN_ONLY / operator auth | REQUIRES_FUTURE_ADAPTER |
| WorkflowEngine event actions | Per-action matrix above | REQUIRES_FUTURE_MIGRATION |

---

## Agent registry (recommendation — not registered in A1)

| Field | Proposed **SDR Assist** (future) |
|-------|----------------------------------|
| Domain | Sales OS |
| Allowed | Research, draft, score recommend |
| Approval boundary | All sends, CRM mutations, stage changes |
| Prohibited | Delete records, pricing, autonomous send |

Temporary Cursor sprint agents ≠ runtime agents.

---

## Verdict

**Agent Governance Boundary: DEFINED**
