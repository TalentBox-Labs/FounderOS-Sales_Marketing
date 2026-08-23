# A4 — Existing Capability Map (NOVA)

**Sprint:** SALES A4 — LeadScorer / Contact.status Human Gate  
**Date:** 2026-08-13  
**Auditor:** NOVA (Existing Capability Auditor)  
**Scope:** Lead scoring, qualification logic, `Contact.status` mutation, runner/API, persistence, audit, validation, tests

---

## Executive Summary

| Question | Answer |
|----------|--------|
| **Primary LeadScorer location** | `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing/revenue_os/services/lead_scoring_service.py` — class `LeadScorer`, functions `score_contact`, `score_contacts_batch` |
| **Known governance gap** | `LeadScorer.update_contact_status` silently mutates `Contact.status` on score (≥70 → `qualified`, ≥40 → `prospect`, else `lead`) without human gate — authority debt C12 |
| **Duplicate scorer** | `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing/revenue_os/services/scoring_service.py` — simpler `score_contact(db, contact_id)`; score-only, no status mutation in service (but Celery task mutates status separately) |
| **Runner contact status PATCH** | **NOT_IMPLEMENTED** — no human-gated status endpoint (A3 deal-stage pattern exists; contact status does not) |
| **Dedicated scoring tests** | **NOT_IMPLEMENTED** — zero tests for `LeadScorer`, Hermes score endpoints, or status promotion |

---

## Classification Legend

| Tag | Meaning |
|-----|---------|
| **LIVE** | Implemented, wired, used in runtime paths |
| **PARTIAL** | Works but incomplete, ungated, or inconsistent with authority contract |
| **API_ONLY** | Endpoint/service exists; not primary Sales runner path or no UI |
| **PLACEHOLDER** | Stub, in-memory, or demo-only |
| **LEGACY** | Superseded path still present |
| **DUPLICATE** | Competing implementation for same concern |
| **NOT_IMPLEMENTED** | Documented/expected but no code |

---

## 1. Core Scoring & Qualification

| Artifact | Path | Class / Function | Classification | Notes |
|----------|------|------------------|----------------|-------|
| **LeadScorer (canonical)** | `revenue_os/services/lead_scoring_service.py` | `LeadScorer` | **LIVE** | Source weights, engagement, company fit, timing; 0–100 score |
| Score calculation | same | `LeadScorer.calculate_score(contact, company_context?)` | **LIVE** | Does not persist; safe to keep **AUTONOMOUS_ALLOWED** |
| Status promotion from score | same | `LeadScorer.update_contact_status(contact, new_score)` | **LIVE** / **PARTIAL** | **Gap:** auto-writes status; no approval queue; logs only |
| Single contact score+status | same | `score_contact(db, contact, company_context?)` | **LIVE** / **PARTIAL** | Sets `contact.lead_score` + calls `update_contact_status` |
| Batch scoring | same | `score_contacts_batch(db, contact_ids, company_context?)` | **LIVE** | Returns `newly_qualified` count; commits batch |
| Score query helpers | same | `get_contacts_by_score`, `get_score_distribution` | **LIVE** | Read-only |
| **Legacy/simple scorer** | `revenue_os/services/scoring_service.py` | `score_contact(db, contact_id)` | **DUPLICATE** | Field checklist scorer; commits score only |
| Contact model fields | `revenue_os/models/contact.py` | `Contact.status`, `Contact.lead_score`, `ContactStatus` enum | **LIVE** | SoT: `lead`, `prospect`, `qualified`, `customer`, … |
| Hermes qualify threshold constant | `revenue_os/services/hermes_planner.py` | `QUALIFY_SCORE_THRESHOLD = 70` | **LIVE** | Aligns with LeadScorer ≥70 → qualified |
| Marketing subscriber score | `revenue_os/marketing/lead_nurturing.py` | `SubscriberProfile.lead_score`, `segment_by_lead_score` | **PLACEHOLDER** | In-memory marketing domain; not CRM `Contact` |
| Marketing email LeadScore | `revenue_os/marketing/email_automation.py` | `LeadScore` dataclass, `_lead_scores` dict | **PLACEHOLDER** | In-memory; not wired to Revenue CRM |
| LLM lead score (no CRM write) | `revenue_os/agents/sdr_agent.py` | `score_and_enrich_lead`, `_fallback_score` | **API_ONLY** | Returns JSON score; does not update `Contact` |
| ICP fit on enrich | `revenue_os/services/linkedin_enrichment.py` (via CRM enrich route) | `score_icp_fit` | **PARTIAL** | Enrichment-side fit score; separate from LeadScorer |
| Qualification rate KPIs | `revenue_os/executive/kpis.py`, `revenue_os/executive/insights.py` | KPI / insight builders | **LIVE** | Read `Contact.status`, `get_score_distribution` |
| Analytics qualify rate | `revenue_os/services/analytics_depth.py` | source qualify metrics | **LIVE** | Reads status; no mutation |

---

## 2. Contact.status Mutation Paths

All paths that **write** `Contact.status` today:

| # | Path | Function / Handler | Trigger | Classification | Human gate? |
|---|------|-------------------|---------|----------------|-------------|
| 1 | `revenue_os/services/lead_scoring_service.py` | `LeadScorer.update_contact_status` | Score thresholds 70/40 | **LIVE** / **PARTIAL** | **No** — A4 target |
| 2 | same | `score_contact` → (1) | Hermes API, heartbeat, planner score step | **LIVE** / **PARTIAL** | **No** |
| 3 | `revenue_os/services/hermes_planner.py` | `action_qualify_high_scorers` | `lead_score >= threshold` + status in LEAD/PROSPECT | **LIVE** / **PARTIAL** | **No** (sets QUALIFIED directly); files outreach approvals only |
| 4 | `revenue_os/tasks/leads.py` | `enrich_lead` Celery task | `score >= 50` and status == LEAD | **LEGACY** / **DUPLICATE** | **No**; uses `scoring_service` not LeadScorer |
| 5 | `runner_api_routers/n8n_webhooks.py` | `receive_n8n_event` (`meeting.booked`) | Inbound n8n webhook | **LIVE** / **PARTIAL** | **No** |
| 6 | `revenue_os/api/v1/contacts.py` | `create_contact`, `update_contact` | Manual API body `status` | **API_ONLY** | **No** (JWT Revenue API, not runner gate) |
| 7 | `runner_api_routers/crm.py` | `create_contact` | Request `status` at create | **LIVE** | **No** (human sets at create; no promotion gate) |
| 8 | `scripts/init_demo_db.py` | seed data | Demo bootstrap | **PLACEHOLDER** | N/A |

**Read-only / gate consumers (no status write):**

| Path | Usage |
|------|-------|
| `runner_api_routers/hermes.py` `qualify_contacts_endpoint` | Requires `status == qualified` before deal create |
| `revenue_os/services/deal_automation_service.py` `create_deal_from_contact` | Returns None if not qualified |
| `revenue_os/services/lead_prospecting_service.py` | Filters by `status` + `lead_score` |
| `revenue_os/services/followups.py`, `revenue_os/services/copilot.py` | Lists qualified / stale by status+score |

**NOT_IMPLEMENTED:** Runner `PATCH /api/v1/crm/contacts/{id}/status` with `requested_by` + `is_human_approver` (A3 deal-stage analogue).

---

## 3. Runner / API Handlers

| Endpoint / Router | Path | Handler | Classification | Reuse for A4 |
|-------------------|------|---------|----------------|--------------|
| Hermes score batch | `runner_api_routers/hermes.py` | `POST /api/v1/hermes/score-contacts` → `score_contacts_batch` | **LIVE** / **PARTIAL** | Keep endpoint; gate status side-effect |
| Hermes lead list by score | same | `GET /api/v1/hermes/lead-scores` | **LIVE** | Read-only reuse |
| Hermes score distribution | same | `GET /api/v1/hermes/score-distribution` | **LIVE** | Read-only reuse |
| Hermes qualify → deals | same | `POST /api/v1/hermes/qualify-contacts` | **LIVE** | Downstream of status; no auto-promote |
| Hermes SDR outreach | same | `POST /api/v1/hermes/sdr-outreach` | **LIVE** | Checks `status == qualified` |
| CRM contacts CRUD | `runner_api_routers/crm.py` | `GET/POST /api/v1/crm/contacts` | **LIVE** | Add status PATCH here (mirror A3) |
| CRM deal stage (A3 pattern) | same | `PATCH /api/v1/crm/deals/{id}/stage` | **LIVE** | **Template for A4** — `is_human_approver`, EventBus |
| Approvals queue | `runner_api_routers/approvals.py` | `GET/POST /api/v1/approvals`, approve/reject | **LIVE** | Extend executors for `promote_contact_status` |
| n8n inbound | `runner_api_routers/n8n_webhooks.py` | `POST /webhooks/n8n/{event_name}` | **LIVE** / **PARTIAL** | `meeting.booked` auto-qualifies — needs gate or proposal |
| Prospecting (score filter) | `runner_api_routers/prospecting.py` | plan/import/execute | **LIVE** | Consumes `lead_score`/`status`; no mutation |
| Revenue JWT contacts | `revenue_os/api/v1/contacts.py` | CRUD + auto-score on create | **API_ONLY** / **DUPLICATE** | Uses legacy `scoring_service` |
| Revenue agents score | `revenue_os/api/v1/agents.py` | `POST /agents/score-lead` | **API_ONLY** | LLM JSON only |
| Orchestration voice qualify | `runner_api_routers/orchestration.py` | `run_voice_qualification` flag | **PLACEHOLDER** | GTM orchestration flag; no CRM status write |
| Router registration | `runner_api.py` | `app.include_router(hermes_router)` | **LIVE** | No change needed |

---

## 4. Persistence

| Concern | Location | Classification | Notes |
|---------|----------|----------------|-------|
| Contact row | `revenue_os/models/contact.py` → table `contacts` | **LIVE** | `status` Enum, `lead_score` Integer default 0 |
| Approval proposals | `revenue_os/models/approvals.py` → `approval_requests` | **LIVE** | JSON payload; no `promote_contact_status` executor yet |
| Agent audit trail | `revenue_os/models/automation_state.py` → `AgentActionLog` | **LIVE** | Via `log_agent_action` |
| Heartbeat runs | same → `heartbeat_runs` | **LIVE** | Scoring job persisted |
| Goal steps | `revenue_os/models/goals.py` | **LIVE** | Hermes planner actions including qualify |
| Migrations | SQLAlchemy models in repo | **LIVE** | A4 should not require schema change if reusing approvals + existing columns |

---

## 5. Audit & Event Hooks

| Hook | Path | Classification | Wired from LeadScorer? |
|------|------|----------------|------------------------|
| `emit_lead_scored` | `revenue_os/automation/events.py` | **PARTIAL** | **No** — defined but never called from scoring service |
| `emit_contact_qualified` | same | **LIVE** | Called from `hermes_planner.action_qualify_high_scorers` only |
| `emit_contact_status_changed` | same | **NOT_IMPLEMENTED** (caller) | Defined; no production caller |
| `EventType.LEAD_SCORED` | same | **LIVE** | n8n `email.replied` path publishes directly |
| `EventType.LEAD_QUALIFIED` | same | **LIVE** | n8n `meeting.booked`, Hermes planner |
| `EventType.CONTACT_STATUS_CHANGED` | same | **NOT_IMPLEMENTED** (caller) | Enum exists; unused |
| `log_agent_action` | `revenue_os/services/activity_log.py` | **LIVE** | Heartbeat `lead_scored`; Hermes goals; n8n inbound |
| LeadScorer status change | `lead_scoring_service.py` | **PARTIAL** | `logger.info` only — no EventBus / activity log |
| A3 deal stage EventBus pattern | `runner_api_routers/crm.py` `update_deal_stage` | **LIVE** | **Reuse:** publish with `requested_by`, old/new status |

---

## 6. Validation & Authority

| Artifact | Path | Classification | A4 relevance |
|----------|------|----------------|--------------|
| Human approver check | `src/tools/editorial_approval.py` | `is_human_approver(approver)` | **LIVE** | Used by A3 deal stage; **reuse for contact status** |
| Authority contract | `docs/sales/SALES_AGENT_AUTHORITY_CONTRACT_v1.0.md` | doc | Lead scoring → status = **HUMAN_APPROVAL_REQUIRED** |
| Authority matrix | `docs/sales/SALES_AGENT_AUTHORITY_MATRIX.md` | doc | Names `LeadScorer.update_contact_status` as gap |
| API key auth | `runner_api_routers/utils.py` | `_verify_api_key` | **LIVE** | Hermes + CRM routes |
| Hermes Pydantic limits | `runner_api_routers/hermes.py` | `ScoreContactsRequest` max 1000 ids | **LIVE** | Batch validation exists |
| Contact status enum validation | `runner_api_routers/crm.py` | `ContactStatus(req.status)` on create | **LIVE** | Extend for PATCH |
| Approval executors registry | `revenue_os/services/approvals.py` | `EXECUTORS` dict | **LIVE** | Today: email, deal, LinkedIn — **add status promotion** |

---

## 7. Scheduler & Background Jobs

| Job | Path | Classification | Status mutation? |
|-----|------|----------------|------------------|
| Heartbeat score new leads | `revenue_os/scheduler.py` → `job_score_new_leads` | **LIVE** / **PARTIAL** | Yes — via `lead_scoring_service.score_contact` |
| Hermes goal check | same → `job_hermes_goal_check` | **LIVE** / **PARTIAL** | Yes — `qualify_high_scorers` action |
| Celery enrich lead | `revenue_os/tasks/leads.py` | **LEGACY** | Yes — separate scorer + threshold 50 |
| Planner action registry | `revenue_os/services/hermes_planner.py` | `ACTION_REGISTRY` | **LIVE** | `score_unscored_leads`, `qualify_high_scorers` |

---

## 8. UI & Display (read-only)

| Surface | Path | Classification | Notes |
|---------|------|----------------|-------|
| Sales template | `templates/sales.html` | **LIVE** | Renders `lead.status`, `lead.lead_score`; sort by score |
| Marketing template | `templates/marketing.html` | **LIVE** | Same lead display |
| React Contacts | `frontend/src/pages/Contacts.jsx` | **PARTIAL** | Score bar color ≥70; SPA unmounted per A2 register |
| React ContactDetail | `frontend/src/pages/ContactDetail.jsx` | **PARTIAL** | Shows `lead_score`, status badge |
| React Analytics | `frontend/src/pages/Analytics.jsx` | **PARTIAL** | Score bucket counts |
| Static CRM index | `revenue_os/static/index.html` | **LEGACY** | Displays `lead_score` column |

---

## 9. Tests (existing)

| Test file | Path | Coverage | Classification |
|-----------|------|----------|----------------|
| LeadScorer / Hermes score / status gate | — | — | **NOT_IMPLEMENTED** |
| A3 deal stage (pattern reference) | `tests/test_a3_runner_deal_stage.py` | `apply_deal_stage_update`, `PATCH .../stage`, `is_human_approver` 403 | **LIVE** |
| Human approver unit | `tests/test_editorial_approval.py` | `test_is_human_approver` | **LIVE** |
| Prospecting filters | `tests/test_lead_prospecting_service.py` | `lead_score`, `ContactStatus` in pool query | **LIVE** (indirect) |
| Runner prospecting API | `tests/test_sales_api_runner.py` | `lead_score` in plan mock only | **PARTIAL** |
| Analytics mocks | `tests/test_analytics.py` | `lead_score` + status namespaces | **PARTIAL** |
| Approvals API | — | — | **NOT_IMPLEMENTED** (thin / absent) |

**A4 test gap:** Add `tests/test_a4_runner_contact_status.py` mirroring `tests/test_a3_runner_deal_stage.py`.

---

## 10. Documentation & Governance (reference only)

| Doc | Classification | Relevance |
|-----|----------------|-----------|
| `docs/sales/SALES_A2_IMPLEMENTATION_SEQUENCE.md` | doc | Names A4 as LeadScorer human gate |
| `docs/sales/SALES_A0_SECURITY_GOVERNANCE_AUDIT.md` | doc | HIGH finding on auto status |
| `docs/sales/SALES_A0_WORKFLOW_MAP.md` | doc | Dual scorer conflict noted |
| `docs/HERMES_REVENUE_LAYER.md` | doc | Hermes API contract for scoring |
| `docs/governance/CP1_FOUNDER_OS_PRIORITY_DECISION.md` | doc | A4 = NOW priority |

---

## 11. Recommended Reuse Points for A4

### Keep autonomous (score only)

| Reuse | Path | Function |
|-------|------|----------|
| Score algorithm | `revenue_os/services/lead_scoring_service.py` | `LeadScorer.calculate_score` |
| Persist score | same | Set `contact.lead_score` without status write |
| Batch/read APIs | same + `runner_api_routers/hermes.py` | `score_contacts_batch`, GET lead-scores, score-distribution |
| Heartbeat scoring | `revenue_os/scheduler.py` | `job_score_new_leads` after refactor |

### Gate status promotion (human / approval)

| Reuse | Path | Function / Pattern |
|-------|------|-------------------|
| **Primary refactor target** | `revenue_os/services/lead_scoring_service.py` | Split `update_contact_status` → `recommend_contact_status(score)` + `apply_contact_status_update(db, contact, new_status)` |
| A3 runner gate template | `runner_api_routers/crm.py` | `update_deal_stage` — `requested_by`, `is_human_approver`, EventBus payload |
| A3 service template | `revenue_os/services/deal_automation_service.py` | `apply_deal_stage_update` — single apply function, noop/same-status, terminal guards |
| Human identity validation | `src/tools/editorial_approval.py` | `is_human_approver` |
| Approval queue | `revenue_os/services/approvals.py` | `request_approval`, `decide`, new `EXECUTORS["promote_contact_status"]` |
| Approvals API | `runner_api_routers/approvals.py` | Existing list/create/approve/reject |
| Status change events | `revenue_os/automation/events.py` | `emit_contact_status_changed`, `emit_lead_scored` (wire on apply) |
| Audit | `revenue_os/services/activity_log.py` | `log_agent_action(actor, action_type="contact_status_promoted", ...)` |

### Consolidate / deprecate (post-gate)

| Action | Path | Reason |
|--------|------|--------|
| Route Celery through LeadScorer | `revenue_os/tasks/leads.py` | **DUPLICATE** scorer + ungated promote |
| Unify Revenue API create scoring | `revenue_os/api/v1/contacts.py` | Uses `scoring_service` not LeadScorer |
| Gate Hermes planner qualify | `revenue_os/services/hermes_planner.py` | `action_qualify_high_scorers` direct status write |
| Gate n8n meeting.booked | `runner_api_routers/n8n_webhooks.py` | Auto-qualify on webhook |
| Document marketing LeadScore boundary | `revenue_os/marketing/email_automation.py` | Not CRM — no A4 change |

### New surface (expected A4 deliverable)

| Add | Modeled on |
|-----|------------|
| `PATCH /api/v1/crm/contacts/{contact_id}/status` | `PATCH /api/v1/crm/deals/{deal_id}/stage` |
| Service `apply_contact_status_update(db, contact, new_status)` | `apply_deal_stage_update` |
| Tests `tests/test_a4_runner_contact_status.py` | `tests/test_a3_runner_deal_stage.py` |

---

## 12. Capability Reconciliation Matrix

| ID (A2) | Name | Overall state | Primary code | A4 action |
|---------|------|---------------|--------------|-----------|
| C12 | Hermes score/qualify | **LIVE** / **PARTIAL** | `lead_scoring_service` + `hermes.py` | Gate status; keep score LIVE |
| C13 | Approvals queue | **LIVE** | `approvals.py` | Add status promotion executor |
| C03 | Contacts CRM | **LIVE** | `crm.py` | Add status PATCH |
| — | Simple scorer | **DUPLICATE** | `scoring_service.py` | Consolidate or isolate |
| — | Celery enrich | **LEGACY** | `tasks/leads.py` | Remove direct status promote |
| — | Contact status PATCH | **NOT_IMPLEMENTED** | — | **BUILD** (A4) |
| — | Scoring unit tests | **NOT_IMPLEMENTED** | — | **ADD** |

---

## 13. Quick Reference — File Index

```
PRIMARY
  revenue_os/services/lead_scoring_service.py     LeadScorer, score_contact, score_contacts_batch
  revenue_os/models/contact.py                    ContactStatus, Contact.lead_score, Contact.status

DUPLICATE / LEGACY
  revenue_os/services/scoring_service.py          alternate score_contact
  revenue_os/tasks/leads.py                       Celery enrich + status promote

API / RUNNER
  runner_api_routers/hermes.py                    POST score-contacts, GET lead-scores, POST qualify-contacts
  runner_api_routers/crm.py                       contacts CRUD (no status PATCH yet)
  runner_api_routers/approvals.py                 human approval queue API
  runner_api_routers/n8n_webhooks.py              meeting.booked → qualified
  revenue_os/api/v1/contacts.py                   JWT contacts + legacy scorer on create

ORCHESTRATION
  revenue_os/services/hermes_planner.py           score_unscored_leads, qualify_high_scorers
  revenue_os/scheduler.py                         heartbeat job_score_new_leads

EVENTS / AUDIT
  revenue_os/automation/events.py                 LEAD_SCORED, LEAD_QUALIFIED, CONTACT_STATUS_CHANGED
  revenue_os/services/activity_log.py             log_agent_action

GATE PATTERN (A3 → A4)
  runner_api_routers/crm.py                       update_deal_stage
  revenue_os/services/deal_automation_service.py  apply_deal_stage_update
  src/tools/editorial_approval.py                 is_human_approver

TESTS (existing)
  tests/test_a3_runner_deal_stage.py              pattern to mirror
  tests/test_editorial_approval.py                is_human_approver
  tests/test_lead_prospecting_service.py            score/status filters only
```

---

**NOVA verdict:** A4 is **COMPLETE_EXISTING** infrastructure — scoring engine, Hermes APIs, approvals queue, A3 human-gate pattern, and event/audit primitives all exist. The sprint work is to **stop silent promotion** in `LeadScorer.update_contact_status` and parallel paths, **centralize apply** behind human gate + approvals, and **add runner tests** where none exist today.
