# 10 — Revenue OS

Evidence of CRM, sales, prospecting, and revenue intelligence components.

---

## Package entry

| Item | Evidence |
|------|----------|
| Standalone FastAPI | `revenue_os/main.py` (`title="Revenue OS"`, `version="0.1.0"`) |
| Combined hosting | Imported/used extensively by `runner_api.py` and `runner_api_routers/*` |
| Config | `revenue_os/config.py` (`Settings`, `DATABASE_URL`, AI keys, Redis, Chroma, n8n, etc.) |
| DB | `revenue_os/database.py` |

---

## CRM

| Item | Evidence |
|------|----------|
| Models | `Company`, `Contact`, `Deal`, `Pipeline`, `Activity`, … |
| Runner CRM API | `runner_api_routers/crm.py` → `/api/v1/crm` |
| JWT CRM API | `revenue_os/api/v1/contacts.py`, `companies.py`, `deals.py` |
| Services | `contact_service.py`, `deal_service.py` |
| Frontend | `frontend/src/pages/Contacts.jsx`, `ContactDetail.jsx`, `Deals.jsx`, `DealDetail.jsx`, `Dashboard.jsx` |
| UI template | `templates/sales.html` |

---

## Deals / Pipeline

| Item | Evidence |
|------|----------|
| Models | `revenue_os/models/deal.py` |
| CRM pipeline endpoint | `GET /api/v1/crm/pipeline` |
| Deal automation | `revenue_os/services/deal_automation_service.py` |
| Hermes pipeline health/forecast | `/api/v1/hermes/pipeline-health`, `/pipeline-forecast`, `/deals-at-risk` |
| Forecasting deal win probability | `/api/v1/forecasting/deal-win-probability/{deal_id}` |

---

## Contacts

| Item | Evidence |
|------|----------|
| Model + enums | `Contact`, `ContactStatus`, `ContactSource`, `Industry` |
| Enrich endpoint | `POST /api/v1/crm/contacts/{contact_id}/enrich` |
| LinkedIn enrichment service | `revenue_os/services/linkedin_enrichment.py` |
| Followups | `GET /api/v1/crm/followups`; `services/followups.py` |

---

## Prospecting

| Item | Evidence |
|------|----------|
| Service | `revenue_os/services/lead_prospecting_service.py` |
| Runner API | `runner_api_routers/prospecting.py` |
| Revenue OS API | `revenue_os/api/v1/prospecting.py` |
| Presets file usage | `output/sales/prospecting_presets.json` (observed under `output/sales/`) |
| Env thresholds | `PROSPECT_*`, MCP/scraper keys in `.env.example` |
| Tests | `tests/test_lead_prospecting_service.py`, `tests/test_prospecting_ui.py`, `tests/test_sales_api_runner.py` |

---

## Sales agents / AI sales assists

| Item | Evidence |
|------|----------|
| Sales agents service | `revenue_os/services/sales_agents.py` |
| Agents sales routes | `/api/v1/agents/sales/{contact_id}/*` |
| AI service | `revenue_os/services/ai_service.py` |
| SDR crew | `src/sdr_crew.py` via Hermes |
| Revenue OS agents API | `/api/v1/agents/score-lead`, `outreach-sequence`, … |

---

## Outreach

| Item | Evidence |
|------|----------|
| Models | `OutreachSequence`, `SequenceStep`, `Activity` |
| Runner API | `runner_api_routers/outreach.py` |
| JWT API | `revenue_os/api/v1/outreach.py` |
| Service | `outreach_service.py` (`schedule_contact_sequence`) |
| Celery tasks | `revenue_os/tasks/outreach.py` |

---

## Automation

| Item | Evidence |
|------|----------|
| Automation package | `revenue_os/automation/{workflows,events,actions,init}.py` |
| API | `/api/v1/automation/*` |
| Models | `Workflow*`, `Trigger`, `Action`, `WorkflowDefinitionRecord` |
| Heartbeat | `revenue_os/scheduler.py` |
| n8n | `integrations/n8n.py`, `/webhooks/n8n` |

---

## Scoring

| Item | Evidence |
|------|----------|
| Lead scoring | `lead_scoring_service.py`, `scoring_service.py` |
| Hermes score endpoints | `/api/v1/hermes/score-contacts`, `/lead-scores`, `/score-distribution`, `/qualify-contacts` |
| Heartbeat job | `score_new_leads` |

---

## Revenue intelligence / executive / forecasting

| Item | Evidence |
|------|----------|
| Revenue intelligence service | `revenue_os/services/revenue_intelligence.py` (dashboard stats in `main.py`) |
| Paperclip executive API | `runner_api_routers/paperclip.py` |
| Executive package | `revenue_os/executive/{kpis,insights}.py` |
| Forecasting package | `revenue_os/forecasting/{models,scenarios}.py` |
| Forecasting API | `runner_api_routers/forecasting.py` |
| Analytics | `revenue_os/analytics/*`, analytics routers |
| Reporting | `revenue_os/reporting/*`, reporting router |
| Docs | `docs/HERMES_REVENUE_LAYER.md`, `PAPERCLIP_EXECUTIVE_LAYER.md`, `FORECASTING_ML_SCENARIOS.md` |

---

## Approvals / goals

| Item | Evidence |
|------|----------|
| Approvals API + model | `/api/v1/approvals`, `ApprovalRequest` |
| Hermes goals | `/api/v1/hermes/goals`, models `Goal`/`GoalStep`, `hermes_planner.py` |

---

## Customer success (revenue-adjacent)

| Item | Evidence |
|------|----------|
| CSM API | `/api/v1/csm/*` |
| Package | `revenue_os/customer_success/` |
| Docs | `docs/CSM_CUSTOMER_SUCCESS.md` |
