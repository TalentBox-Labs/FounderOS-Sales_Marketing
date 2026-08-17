# M0.5 M0 Gap Reconciliation

**Sprint:** REV-ORCH M0.5  
**Date:** 2026-08-17  
**Method:** M0 artifact wording + current implementation. No silent reinterpretation.

---

## Source artifacts

- `docs/revenue/orchestration/m0/M0_IMPLEMENTATION_READINESS.md`
- `docs/revenue/orchestration/m0/M0_TENANT_CONTEXT_PROPAGATION_AUDIT.md`
- `docs/revenue/orchestration/m0/M0_STALE_AUTHORITY_EXECUTION_CONTRACT.md`
- `docs/revenue/orchestration/m0/M0_APPROVAL_REQUEST_REUSE_ATTESTATION.md`
- `docs/revenue/orchestration/m0/M0_API_SURFACE_DECISION.md`
- `docs/revenue/orchestration/m0/M0_CREWAI_LEGACY_ATTESTATION.md`
- `docs/revenue/orchestration/m0/M0_SALES_AGENT_MODULE_RECONCILIATION.md`
- `docs/revenue/orchestration/m0/M0_AI_AUTHORITY_CONTRACT.md`

M0 overall: **CONDITIONAL READY**; “None critical” blockers before M1; listed items as **M1 sprint scope**.

---

| M0 gap (verbatim sense) | M0 wording | Implementation check | Classification |
|-------------------------|------------|----------------------|----------------|
| sales_agents ID-only contact lookup / insufficient tenant scope | Residual **critical**; “fix in M1”; “Add TenantContext to sales agent routes (M1 sprint scope)” | `_load_contact(db, contact_id)` uses `db.get(Contact, cid)` — confirmed | **MUST_FIX_IN_M1** |
| HeartbeatScheduler / background lose TenantContext | Residual **high**; global Contact query | `job_score_new_leads` queries Contact without org filter — confirmed | **SAFE_TO_DEFER** (not on M1 email slice; still required before multi-tenant heartbeat send) |
| ApprovalRequest tenant linkage incomplete | No organization_id column; payload can carry org | Model has no org column — confirmed. AgentActionLog **does** have organization_id | **MUST_FIX_IN_M1** (payload + execute-time Contact.organization_id join; no new table required) |
| Stale authority revalidation before delayed execution | Contract DEFINED; decide() is sync so T1≈T2 for M1 approve-send | `decide()` executes immediately; no membership re-check — confirmed | **MUST_FIX_IN_M1** for outbound execute (membership + org + idempotency). Full scheduled Activity revalidation **SAFE_TO_DEFER** |
| Human vs agent approver classification | Residual high: `is_human_approver` does not block names like `cold_email_agent`; approve API `decided_by` client field | Forbidden set is exact tokens (`openai`, `crewai`, `agent:` prefix) — `cold_email_agent` would pass — confirmed | **MUST_FIX_IN_M1** (server-bind decided_by from IdentityContext; do not trust body) |
| Approval vs execution separation | PARTIAL — same call stack | `decide()` sets approved then calls executor — confirmed | **SAFE_TO_DEFER** as split queue; **MUST_FIX_IN_M1** only idempotency so retry ≠ second send |
| Dual API surface | Canonical runner_api | Dockerfile CMD runner_api; CrewAI unmounted — confirmed | **ALREADY_MITIGATED** |
| CrewAI HTTP bypass | QUARANTINED | `v1_router` does not include agents_router — confirmed | **ALREADY_MITIGATED** |
| WorkflowOrchestrator stub `_execute_agent` | M1 wire or document interim direct routes | Placeholder return `action_by_{agent}` — confirmed | **MUST_FIX_IN_M1** if using workflow execute API; **SAFE_TO_DEFER** if M1 uses explicit sequential services on sales routes (still one orchestrator conceptually) |
| General LLM tool calling | PROHIBITED_FOR_M1 | No `tools=` in ai_service — confirmed | **ALREADY_MITIGATED** |
| OpenAI/n8n GLOBAL_BY_DESIGN | SAFE_WITH_M1_RESTRICTIONS | env keys — confirmed | **SAFE_TO_DEFER** (per-tenant keys = later autonomy sprint) |
| research_contact Activity NOTE without human gate | M0: acceptable enrichment log; add tenant guard M1 | `_log_note` + commit — confirmed | **MUST_FIX_IN_M1** (tenant only). Treating NOTE as SoT mutation: **NOT_CONFIRMED** as privileged (not Contact.status) |
| build_followup_sequence persists OutreachSequence | M0 FUTURE / not M1 | Creates OutreachSequence — confirmed | **SAFE_TO_DEFER** (out of M1; must fix before FUTURE_REUSE) |
| Celery `score_lead_background` | LEGACY propose-only | Still imports sdr_agent — confirmed | **SAFE_TO_DEFER** (do not enqueue from M1) |
| DecisionManager parallel authority | LEGACY | Still on runner_api `/decisions` | **SAFE_TO_DEFER** (do not use in M1); deprecate later |

---

## MUST_FIX_BEFORE_M1

**NONE.** M0 attested no critical pre-M1 blockers; CrewAI HTTP already contained.

---

## MUST_FIX_IN_M1

1. Tenant-scoped sales_agents / agents routes (ID-only lookup)
2. Approval payload org + execute-time org validation
3. Outbound idempotency + skip if already executed
4. Server-bound human `decided_by` on approve (do not trust client spoof)
5. AgentActionLog.organization_id populated on worker/approval/n8n events

---

## SAFE_TO_DEFER

Heartbeat org isolation; Celery CrewAI; ApprovalRequest new column; workflow stub if unused; follow-up sequence persist; per-tenant OpenAI; DecisionManager removal; scheduled Activity stale-authority beyond sync approve-send.

---

## ALREADY_MITIGATED

Dual API canonicalization; CrewAI HTTP quarantine; tool-calling absence; S3.5/S4.5 CRM/connector tests still green independently.

---

## NOT_CONFIRMED

That Activity NOTE from research is a frozen-authority violation — M0 classified it as enrichment logging, not A4.

---

*End of M0.5 M0 Gap Reconciliation*
