# M0 Sales Agent Module Reconciliation

**Sprint:** REV-ORCH M0  
**Date:** 2026-08-17

---

## Module Inventory

All modules in `revenue_os/services/sales_agents.py`:

| Module | Constant | Function | Classification | M1 |
|--------|----------|----------|----------------|-----|
| ICP Research | `AGENT_ICP_RESEARCH` | `research_contact` | **REUSE_AS_AI_NODE** | Yes |
| Cold Email | `AGENT_COLD_EMAIL` | `draft_cold_email` | **REUSE_AS_AI_NODE** | Yes |
| LinkedIn Opener | `AGENT_LINKEDIN_OPENER` | `draft_linkedin_opener` | **REUSE_AS_AI_NODE** | Optional |
| Follow-Up Sequence | `AGENT_FOLLOWUP_SEQUENCE` | `build_followup_sequence` | **REUSE_AS_AI_NODE** | Expansion |
| Objection Handler | `AGENT_OBJECTION_HANDLER` | `handle_latest_reply` | **REUSE_AS_AI_NODE** | Expansion |

---

## Compatibility Assessment

| Criterion | ICP Research | Cold Email | LinkedIn | Follow-up | Objection |
|-----------|--------------|------------|----------|-----------|-----------|
| Proposal-only outbound | N/A | **Yes** | **Yes** | **Yes** | **Yes** |
| ApprovalRequest | No (Activity note) | **Yes** | **Yes** | **Yes** | **Yes** |
| TenantContext | **Gap** | **Gap** | **Gap** | **Gap** | **Gap** |
| AIService usage | Partial | **Yes** | **Yes** | **Yes** | **Yes** |
| Direct send | **No** | **No** | **No** | **No** | **No** |
| Audit | Activity NOTE | ApprovalRequest | ApprovalRequest | ApprovalRequest | ApprovalRequest |

---

## Issues

| Module | Issue | M0 action |
|--------|-------|-----------|
| All | ID-only contact lookup — cross-tenant risk | Document; fix in M1 |
| `research_contact` | Writes Activity without human gate | Acceptable (enrichment log); add tenant guard M1 |
| None | Unsafe direct execution | None quarantined |

---

## Not Required for M1 MVP

- `AGENT_LINKEDIN_OPENER` — optional channel
- `AGENT_FOLLOWUP_SEQUENCE` — expansion sprint
- `AGENT_OBJECTION_HANDLER` — requires inbound reply flow

---

## Deprecated / Legacy (not sales_agents)

| Module | Classification |
|--------|----------------|
| CrewAI `sdr_agent.generate_outreach_sequence` | **LEGACY** — quarantined |
| CrewAI `sdr_agent.score_and_enrich_lead` | **LEGACY** — Celery only |

---

## Recommended Reuse for M1 MVP

1. `research_contact` — enrich step
2. `draft_cold_email` — outreach draft step
3. `lead_scoring_service.score_contact` — deterministic recommend (not in sales_agents but paired)

---

*End of M0 Sales Agent Module Reconciliation*
