# REV-ORCH M1.5 — Baseline Manifest

**STATUS: FROZEN**  
**Parent commit:** `d36d7a2` (`complete REV-ORCH M1 research-to-approved-outreach and M1.1 reconciliation`)  
**Branch:** `develop`  
**Baseline version:** v1.0

---

## Canonical Implementation Files

| File | Role |
|------|------|
| `revenue_os/agents/orchestration.py` | WorkflowOrchestrator + M1 registration |
| `revenue_os/services/revenue_orchestration_service.py` | Subordinate M1 workflow |
| `revenue_os/services/revenue_workers.py` | Research/Personalization workers |
| `revenue_os/services/approvals.py` | ApprovalRequest authority |
| `revenue_os/services/activity_log.py` | AgentActionLog provenance |
| `revenue_os/services/tenant_scoped_access.py` | Tenant-scoped lookups |
| `revenue_os/services/sales_agents.py` | Legacy sales (contained) |
| `runner_api.py` | App entry + workflow seed |
| `runner_api_routers/revenue_orchestration.py` | Canonical API |
| `runner_api_routers/approvals.py` | Human approve/reject |
| `runner_api_routers/agents.py` | Legacy sales routes |

## Freeze Tests

| Suite | Purpose |
|-------|---------|
| `tests/test_rev_orch_m1_5_research_to_outreach_baseline_freeze.py` | M1.5 freeze contract |
| `tests/test_rev_orch_m1_1_orchestrator_reconciliation.py` | Orchestrator wiring |
| `tests/test_rev_orch_m1_research_to_outreach.py` | M1 vertical slice |
| `tests/test_rev_orch_m0_5_authority_baseline_freeze.py` | M0.5 baseline |
| `tests/test_rev_orch_m0_authority_containment.py` | M0 authority |

## Frozen Contracts Depended Upon

- SaaS S2/S2.5 TenantContext
- SaaS S3/S3.5 CRM tenant isolation
- SaaS S4/S4.5 integration tenant isolation
- UI1.1 mutation authority
- MC04.5 QualifiedDemand
- MC06.5 CommercialOutcome
- A3/A4 Contact/Deal authority

## Change Budget (M1.5)

| Category | Expected |
|----------|----------|
| Feature code changes | 0 |
| Runtime changes | 0 |
| Migrations | 0 |
| New SoTs | 0 |
| Credentials | 0 |

M1.5 adds: freeze tests + documentation only.

## Known Pre-Existing Debt

- 8 historical crews/utilities test failures
- 12 cockpit template failures (`cockpit.html:53`)
- Legacy sales route capability overlap (non-blocking)

## Explicit Non-Goals

M2 features, cockpit fix, new agents, new integrations
