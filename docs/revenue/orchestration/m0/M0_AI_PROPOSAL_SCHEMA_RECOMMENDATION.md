# M0 AI Proposal Schema Recommendation

**Sprint:** REV-ORCH M0  
**Date:** 2026-08-17

---

## Approach

Use existing dict / ApprovalRequest.payload structures. **No new Pydantic models in M0.**

---

## M1 Minimum Structured Outputs

### 1. ResearchProposal (conceptual)

**Producer:** `sales_agents.research_contact`  
**Persisted:** Activity NOTE + return dict (not ApprovalRequest)

| Field | Source | Model control |
|-------|--------|---------------|
| `contact_id` | Server | **Prohibited** |
| `organization_id` | TenantContext | **Prohibited** |
| `signals.job_change` | Enrichment | Read-only |
| `signals.funding_rounds` | Enrichment | Read-only |
| `icp_fit.score` | Deterministic scorer | Read-only |
| `summary` | Generated text | Allowed |

---

### 2. PersonalizationDraft / OutreachDraft

**Producer:** `draft_cold_email`, `draft_linkedin_opener`  
**Persisted:** `ApprovalRequest.payload`

Existing payload shape (from `sales_agents.py`):

```python
{
    "contact_id": str,      # server-set
    "email": str,           # from Contact SoT
    "name": str,
    "template": "ai_cold_email",
    "context": {"body": str}  # AI-generated
}
```

| Field | Model control |
|-------|---------------|
| `body` / message text | **Allowed** |
| `contact_id`, `email` | **Prohibited** — server binds |
| `organization_id` | **Prohibited** — add in M1 |
| `action_type` | **Prohibited** — server sets |

---

### 3. ScoreRecommendation (conceptual)

**Producer:** `lead_scoring_service.score_contact`  
**Persisted:** Contact.lead_score field (suggest path) or return only

| Field | Notes |
|-------|-------|
| `score` | 0–100 |
| `factors` | Deterministic |
| `recommended_status` | **Display only** — must not auto-apply |

---

## Provenance (M1 gap — F2 sprint)

Recommended additions to ApprovalRequest.payload or AgentActionLog.detail:

```python
{
    "ai_provenance": {
        "model": "gpt-4o",
        "prompt_version": "cold_email_v1",
        "input_refs": {"contact_id": "..."},
    }
}
```

---

## Validation Rules (M1)

1. Reject payloads where model-supplied `organization_id` != TenantContext
2. Strip unknown keys from AI JSON before filing ApprovalRequest
3. Max body length enforced server-side

---

## Persistence Map

| Output | Where stored |
|--------|--------------|
| Research signals | Activity NOTE |
| Email draft | ApprovalRequest.payload |
| Approved send result | ApprovalRequest.execution_result + AgentActionLog |
| Scheduled follow-up | Activity |

**No new SoT.**

---

*End of M0 AI Proposal Schema Recommendation*
