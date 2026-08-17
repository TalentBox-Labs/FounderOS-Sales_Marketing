# M0 Implementation Readiness

**Sprint:** REV-ORCH M0  
**Date:** 2026-08-17  
**Overall:** **CONDITIONAL READY** for REV-ORCH M1

---

## Pass Conditions

| Condition | Status |
|-----------|--------|
| Canonical Revenue Orchestrator identified | **PASS** — WorkflowOrchestrator |
| Parallel unsafe orchestration | **CONTAINED** — CrewAI HTTP quarantined |
| CrewAI production bypass | **BLOCKED** on canonical API |
| AI direct business mutation | **PROHIBITED** |
| AI general tool calling | **NOT_IMPLEMENTED / PROHIBITED** |
| ApprovalRequest reuse | **PASS** |
| TenantContext propagation | **DEFINED** (gaps documented) |
| Scheduled authority revalidation | **DEFINED** |
| Canonical API surface | **PASS** — runner_api |
| OpenAI boundary | **SAFE_WITH_M1_RESTRICTIONS** |
| n8n boundary | **SAFE_WITH_M1_RESTRICTIONS** |
| S4.5 preserved | **PASS** |
| S3.5 preserved | **PASS** |
| Human/Service/Agent/AI separation | **PASS** |
| requested_by server binding | **PASS** |
| New SoT | **NO** |
| Frozen contracts unchanged | **PASS** |

---

## M1 Mutation Boundary

### M1 WILL mutate (with gates)

| Object | Mutation | Gate |
|--------|----------|------|
| Activity | NOTE (research), scheduled outbound | Service / post-approval |
| ApprovalRequest | status, execution_result | Human decide |
| AgentActionLog | audit entries | Automatic |

### M1 MUST NOT autonomously mutate

| Object | Contract |
|--------|----------|
| Contact.status | A4 HUMAN_ONLY |
| Deal.stage | A3 HUMAN_ONLY |
| QualifiedDemand accept/reject | MC04.5 |
| CommercialOutcome | MC06.5 |
| closed-won / revenue decision | MC06.5 |

---

## M1 Flow (confirmed)

```
Existing Contact (tenant-scoped lookup — M1 fix)
  → research_contact (enrich + Activity NOTE)
  → score_contact (suggest only)
  → draft_cold_email (AIService → ApprovalRequest)
  → human approve (/api/v1/approvals)
  → n8n send-email + Activity + audit
```

---

## Blockers Before M1

**None critical.** Conditions for M1 start:

1. Add TenantContext to sales agent routes (M1 sprint scope)
2. Wire WorkflowOrchestrator steps OR document direct route as interim subordinate path
3. Add idempotency key on approval execution (M1)
4. Add org validation at outbound execute (M1)

---

## M0 Code Changes

| Change | Purpose |
|--------|---------|
| `revenue_os/api/v1/agents.py` — 410 quarantine | Block CrewAI legacy bypass |

---

## Residual Critical Risks

- sales_agents ID-only contact lookup (cross-tenant until M1 fix)

## Residual High Risks

- HeartbeatScheduler global queries in multi-tenant deployment
- ApprovalRequest lacks organization_id
- Stale authority not revalidated at delayed execution
- env-backed OpenAI/n8n (accepted with restrictions)

---

## Founder Decisions Before M1

1. Confirm M1 MVP channel: email-only vs email + LinkedIn draft
2. Confirm interim orchestration: direct sales routes vs workflow steps first
3. Accept platform-global OpenAI/n8n for MVP or defer M1

---

## Recommended Next Sprint

**REV-ORCH M1 — RESEARCH-TO-APPROVED-OUTREACH**

---

*End of M0 Implementation Readiness*
