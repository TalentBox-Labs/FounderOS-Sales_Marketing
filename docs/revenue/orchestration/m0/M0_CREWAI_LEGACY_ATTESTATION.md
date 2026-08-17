# M0 CrewAI Legacy Attestation

**Sprint:** REV-ORCH M0  
**Date:** 2026-08-17  
**Hard gate:** PASS (contained)

---

## Scope

| Module | Functions |
|--------|-----------|
| `revenue_os/agents/sdr_agent.py` | `score_and_enrich_lead`, `generate_outreach_sequence` |
| `revenue_os/agents/recruiter_agent.py` | `match_candidate_to_job`, `screen_resume` |

---

## Attestation Checklist

### sdr_agent.py

| # | Question | Answer | Evidence |
|---|----------|--------|----------|
| 1 | Imported by production code? | **Yes** — Celery task, legacy API (quarantined) | `revenue_os/tasks/agents.py`, `revenue_os/api/v1/agents.py` |
| 2 | Reachable via route/scheduler/job? | **Legacy API: NO (410)**; **Celery: YES** | M0 quarantine; docker-compose `worker` service |
| 3 | Mutate CRM/domain state directly? | **NO** | Returns JSON dict only |
| 4 | Call connectors directly? | **NO** | LLM only via CrewAI |
| 5 | Bypass ApprovalRequest? | **YES for outreach-sequence** — returns draft JSON without filing approval | `generate_outreach_sequence` — legacy path quarantined |
| 6 | Construct requested_by client-side? | N/A — no requested_by | |
| 7 | Carry TenantContext? | **NO** | No org parameter |
| 8 | Use ConnectorCredentialRecord? | **NO** — env OPENAI/GEMINI | GLOBAL_BY_DESIGN |
| 9 | Write AgentActionLog? | **NO** | |
| 10 | Work outside canonical orchestrator? | **YES** | Direct invoke |

**Classification:** **QUARANTINED** (HTTP routes); Celery path **PRODUCTION_REACHABLE_SAFE** (propose-only, no mutation/send)

### recruiter_agent.py

| # | Question | Answer | Evidence |
|---|----------|--------|----------|
| 1 | Imported by production code? | **Yes** — legacy API only | `revenue_os/api/v1/agents.py` |
| 2 | Reachable? | **NO on canonical API** | Not mounted on runner_api; legacy 410 |
| 3 | Mutate CRM? | **NO** | JSON only |
| 4 | Connectors? | **NO** | LLM only |
| 5 | Bypass ApprovalRequest? | **YES** — N/A for recruiting scope | Out of revenue M1 scope |
| 7 | TenantContext? | **NO** | |
| 10 | Outside orchestrator? | **YES** | Quarantined |

**Classification:** **QUARANTINED**

---

## Production Reachability Matrix

| Entry | Mounted on runner_api? | Docker production? | Status |
|-------|------------------------|-------------------|--------|
| `POST /api/v1/agents/score-lead` (main.py) | **NO** | **NO** — CMD is runner_api | QUARANTINED 410 |
| `POST /api/v1/agents/outreach-sequence` | **NO** | **NO** | QUARANTINED 410 |
| Celery `score_lead_background` | N/A | **YES** — worker service | SAFE (no mutation) |
| `runner_api` sales agents | **YES** | **YES** | Canonical replacement |

---

## M0 Containment Action

1. **`revenue_os/api/v1/__init__.py`** — CrewAI `agents_router` **unmounted** from legacy app (404).
2. **`revenue_os/api/v1/agents.py`** — all CrewAI routes return **HTTP 410 Gone** if re-mounted.

**Not changed:** Celery task (propose-only, no CRM mutation). Documented as legacy bypass; M1 should not enqueue new CrewAI tasks.

---

## CrewAI Production Bypass Verdict

**BLOCKED** on canonical HTTP surface (runner_api + quarantined legacy routes).

**Residual:** Celery worker can still invoke `score_and_enrich_lead` — returns JSON only, does not send or mutate CRM. Classified acceptable for M0; deprecate in F1 sprint.

---

## Recommendation

Do **not** integrate CrewAI into canonical architecture. Use `sales_agents` + `AIService` + `ApprovalRequest` pattern for M1.

---

*End of M0 CrewAI Legacy Attestation*
