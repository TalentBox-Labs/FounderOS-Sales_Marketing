# REV-ORCH M3.5 — Baseline Manifest

## Freeze Identity

- Sprint: REV-ORCH M3.5
- Title: Governed Reply Handling & Qualification Transition Baseline Freeze
- Version: v1.0
- Parent commit: `6b8e58e`
- Branch: `rev-orch-m3-5`

## Canonical M3 Implementation Files

| File | Role |
|------|------|
| `runner_api_routers/n8n_webhooks.py` | Inbound webhook entry, tenant resolution, Activity persistence, deduplication |
| `revenue_os/services/revenue_orchestration_service.py` | wake_inbound_reply_handling, run_inbound_reply_handling, inspect_latest_reply_assessment |
| `revenue_os/agents/orchestration.py` | M3 workflow registration, WorkflowOrchestrator dispatch |
| `revenue_os/services/revenue_workers.py` | run_reply_analysis_worker (SPECIALIZED_AI_WORKER) |
| `revenue_os/services/ai_service.py` | analyze_inbound_reply (LLM classification) |
| `revenue_os/services/reply_routing.py` | route_reply_assessment, merge_opt_out_tag, REPLY_TYPES |
| `runner_api_routers/revenue_orchestration.py` | GET latest-assessment endpoint |
| `revenue_os/services/follow_up_eligibility.py` | Reply-stop and OPT_OUT eligibility checks |

## Orchestrator

- Canonical: `WorkflowOrchestrator.execute_revenue_workflow()`
- M3 Workflow Key: `REV_ORCH_M3_WORKFLOW_KEY = "rev_orch_inbound_reply_handling"`
- M3 Agent Step: `REV_ORCH_M3_AGENT_STEP = "rev_orch_m3_pipeline"`

## Tenant Resolution

- Source: `OrganizationIntegrationBinding` via `resolve_n8n_organization_id(x_n8n_secret=...)`
- Contact scoping: `scoped_contact()` / `get_contact_for_tenant()`

## Deduplication

- Key: `EmailActivity.message_id`
- Sources: `payload.message_id` → `payload.provider_message_id` → `rev-orch-m3:sha256(contact_id:body)[:32]`
- Tenant safety: contact_id in SHA ensures per-tenant uniqueness

## Reply Classification

- Taxonomy: INTERESTED, NEEDS_INFO, OBJECTION, NOT_NOW, NOT_INTERESTED, OPT_OUT, MEETING_INTEREST, UNKNOWN
- Worker: `run_reply_analysis_worker` → `ai_service.analyze_inbound_reply`
- Routing: `route_reply_assessment()` — deterministic policy

## Freeze Tests

- `tests/test_rev_orch_m3_5_governed_reply_baseline_freeze.py` — 30 tests
- `tests/test_rev_orch_m3_governed_reply_handling.py` — 18 tests

## Known Historical Failures (not revenue orchestration)

- test_crews_unit (3 failures)
- test_utilities_unit (5 failures)
- test_mdg1 (1 failure)
- test_orchestration_api (2 collection errors)
- test_prospecting_ui (2 collection errors)

## Explicit Non-Goals

- Booking implementation
- Autonomous CRM mutation
- New persistent SoTs
- New database models/migrations
- New external integrations
- M2.5/M1.5 contract changes
