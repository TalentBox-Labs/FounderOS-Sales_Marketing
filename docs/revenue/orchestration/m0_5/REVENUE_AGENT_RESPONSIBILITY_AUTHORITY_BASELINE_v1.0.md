# Revenue Agent Responsibility & Authority Baseline v1.0

**Sprint:** REV-ORCH M0.5  
**Date:** 2026-08-17  
**Status:** FROZEN architecture baseline (not a SaaS identity/tenant contract supersession)

This freeze **does not** modify S1.5–S4.5, A3.5, A4.5, MC04.5, MC06.5, MDG1.5, UI2.5, OF1.5.

---

## 1. Canonical Revenue Orchestrator

**ONE:** `WorkflowOrchestrator` (`revenue_os/agents/orchestration.py`) on **`runner_api:app`**.

No second revenue orchestrator (Hermes, GTM, n8n, CrewAI, DecisionManager).

---

## 2. Specialized worker taxonomy

See `M0_5_AGENT_TAXONOMY_v1.md`.

| Kind | Count |
|------|-------|
| Autonomous revenue agents | **0** |
| Specialized AI workers | **multiple allowed** |
| M1 specialized workers | **2** (ResearchWorker, PersonalizationWorker) |

**AGENT ≠ AUTHORITY.**

Canonical flow:

```
WorkflowOrchestrator
  → Specialized AI Worker
  → Structured Proposal
  → Policy / Domain Validation
  → ApprovalRequest
  → Human Authority
  → Deterministic Executor
  → Domain Service / n8n
  → Existing SoT
  → Audit / AgentActionLog
```

---

## 3. M1 workers

- ResearchWorker
- PersonalizationWorker (outreach draft)

Deterministic: `linkedin_enrichment`, `lead_scoring_service`, OutreachExecutor (`send_outreach_email`).

---

## 4. Future worker boundaries

Follow-Up, Objection: LIKELY (proposal-only).  
Qualification / Meeting prep / Pipeline recommend: POSSIBLE (recommend only).  
Lead Finder / Appointment Setter / Autonomous Sales Manager: NOT_RECOMMENDED.

---

## 5. Capability matrix

Frozen in `M0_5_AGENT_CAPABILITY_MATRIX_v1.md`. Workers: DENY approve, send, mutate status/stage, accept QD/CO, select tenant, select credential.

---

## 6. Authority denylist

Frozen in `M0_5_AGENT_AUTHORITY_DENYLIST_v1.md`.

---

## 7. Handoffs

```
PEER_TO_PEER_AGENT_AUTHORITY: PROHIBITED
AGENT_HANDOFFS: ORCHESTRATOR_MEDIATED
```

---

## 8. Context boundaries

Minimum-context per worker. No credentials. No unrestricted DB. Frozen in `M0_5_AGENT_CONTEXT_BOUNDARIES.md`.

---

## 9. AI output boundary

Proposals only. Server owns organization_id, requested_by, credentials, approval/execution status. Existing dicts / ApprovalRequest.payload. **No new SoT. No new persistent domain model.**

---

## 10. Human approval boundary

Outbound send requires ApprovalRequest + human `decide()`. Frozen HUMAN_ONLY: Contact.status, Deal.stage, QD accept/reject, CO accept/reject.

---

## 11. Domain mutation boundary

Domain services mutate SoTs. Workers do not.

---

## 12. Connector execution boundary

n8n executes authorized operations. S4.5 tenancy preserved. OpenAI/n8n env keys: SAFE_WITH_M1_RESTRICTIONS. Workers never select credentials.

---

## 13. Audit boundary

AgentActionLog is the AI/worker audit store. Populate `organization_id`. No parallel AI log SoT.

---

## 14. API surface

CANONICAL: `runner_api:app`. LEGACY: `revenue_os.main:app`.

---

## 15. General LLM tool calling

**PROHIBITED_FOR_M1.**

---

*End of Revenue Agent Responsibility & Authority Baseline v1.0*
