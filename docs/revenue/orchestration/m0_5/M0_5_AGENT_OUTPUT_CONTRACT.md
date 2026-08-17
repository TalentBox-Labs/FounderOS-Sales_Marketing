# M0.5 Agent Output Contract

**Sprint:** REV-ORCH M0.5  
**Date:** 2026-08-17

---

## Rule

Specialized workers return **structured proposals**. They do not perform effects.

**No new persistent models.** Use dicts compatible with existing `ApprovalRequest.payload` and function return values (`sales_agents.py`, `ai_service.py`).

---

## Fields the model MUST NOT authoritatively populate

| Field | Who sets it |
|-------|-------------|
| `organization_id` | TenantContext (server) |
| `requested_by` | Server identity / orchestrator |
| `credential_id` | Never in worker output |
| `approval.status` | ApprovalRequest service |
| `execution_result` | Executor |
| `Contact.status` / `Deal.stage` | Domain services after human gate |
| business outcome / won-lost | MC06.5 human |

If the model emits these keys, **strip and ignore**.

---

## ResearchProposal (M1)

Compatible with current `research_contact` return + extra server fields.

```python
{
  "ok": bool,
  "contact_id": str,           # server
  "organization_id": str,      # server
  "signals": {
    "job_change": dict | None,
    "funding_rounds": list,
    "tech_stack": dict,
  },
  "icp_fit": dict | None,      # from deterministic scorer
  "observations": str,         # optional AI summary
  "evidence": list[str],
  "provenance": {
    "worker": "ResearchWorker",
    "enrichment_configured": bool,
  },
  "failure_reason": str | None,
}
```

**Persisted:** AgentActionLog.detail; optional Activity NOTE via **domain service** (not worker authority).

---

## OutreachDraft (M1)

Compatible with current `draft_cold_email` payload.

```python
{
  "ok": bool,
  "contact_id": str,           # server
  "organization_id": str,      # server
  "channel": "email",          # worker recommendation; orchestrator may reject
  "subject": str | None,
  "body": str,                 # AI-generated — only free field
  "rationale": str,
  "source_refs": ["research_id" or "contact_context_hash"],
  "email": str,                # copied from Contact SoT by server, not model
  "name": str,                 # from Contact SoT by server
}
```

**Persisted:** `ApprovalRequest.payload` after orchestrator validation. Not a new table.

---

## FollowUpProposal (post-M1)

```python
{
  "contact_id": str,           # server
  "organization_id": str,      # server
  "proposed_delay_days": int,
  "channel": str,
  "draft": {"subject": str, "body": str},
  "rationale": str,
}
```

Must **not** create `OutreachSequence` rows (current `build_followup_sequence` does — prohibited for worker).

---

## Validation

1. JSON/schema parse failure → worker failure (no approval, no send).
2. Unknown keys stripped.
3. Max body length server-enforced.
4. `organization_id` in payload must equal TenantContext or be overwritten by server.

---

*End of M0.5 Agent Output Contract*
