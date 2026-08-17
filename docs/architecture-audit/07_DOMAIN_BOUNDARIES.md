# 07 — Domain Boundaries

Logical domains inferred from package/router naming and file ownership. No evaluative commentary.

---

## Domain: Content Pipeline (CMS OS)

| Field | Evidence |
|-------|----------|
| **Ownership** | `src/`, `input/`, `output/qa_reports/`, `data/`, `tracker.csv`, pipeline routers/UI |
| **Files** | `src/tools/pipeline_*.py`, validators, crews (`generation_crew`, `editor_crew`, `qa_crew`, `distribution_crew`, `artifact_crew`), `runner_api_routers/pipeline.py`, `ui.py` week pages |
| **Responsibilities** | Week runtime apply; validate; generate draft; edit final; QA reports; promote/go-live helpers |
| **Inbound** | HTTP pipeline routes; CLI `src.main`; orchestrator module |
| **Outbound** | Filesystem writes; optional Google Sheets / Hashnode tools; CrewAI LLM |
| **Shared objects** | `runtime_config.json`, tracker rows, week markdown artifacts |
| **Cross-domain** | Marketing may reuse content outputs; analytics may read metrics snapshots |

---

## Domain: Marketing

| Field | Evidence |
|-------|----------|
| **Ownership** | `src/marketing_crew.py`, marketing YAML, `runner_api_routers/marketing.py`, `seo.py`, `revenue_os/marketing/`, `revenue_os/integrations/social_publisher.py`, `output/marketing/` |
| **Responsibilities** | Multi-channel content generation; dry-run/publish; SEO keywords; email automation modules under `revenue_os/marketing/` |
| **Inbound** | `/marketing/*`, `/api/v1/seo/*`, marketing UI |
| **Outbound** | Social APIs (env-configured); filesystem under `output/marketing` |
| **Shared objects** | Brand/topic request models; status_path artifacts |
| **Cross-domain** | Integrations (Slack/email); analytics spend |

---

## Domain: Revenue / CRM / Sales

| Field | Evidence |
|-------|----------|
| **Ownership** | `revenue_os/models/{contact,deal,activity}.py`, CRM/prospecting/outreach routers, related services |
| **Responsibilities** | Contacts, companies, deals, pipeline views, activities, sequences, prospecting plans/import |
| **Inbound** | `/api/v1/crm/*`, `/api/v1/prospecting/*`, `/api/v1/outreach/*`; also `revenue_os` v1 JWT APIs |
| **Outbound** | DB; enrichment/MCP providers; AI email generation |
| **Shared objects** | `Contact`, `Deal`, `OutreachSequence`, `Activity` |
| **Cross-domain** | Hermes scoring; agents sales helpers; heartbeat lead scoring |

---

## Domain: Hermes / Revenue Intelligence

| Field | Evidence |
|-------|----------|
| **Ownership** | `runner_api_routers/hermes.py`, `goals.py`, `revenue_os/services/{lead_scoring_service,deal_automation_service,hermes_planner,revenue_intelligence}.py`, `models/goals.py` |
| **Responsibilities** | Lead scoring, qualification, pipeline health/forecast, deals-at-risk, SDR outreach, goals |
| **Inbound** | `/api/v1/hermes/*`, `/api/v1/hermes/goals/*` |
| **Outbound** | DB; `SDRCrew` (`src.sdr_crew`); optional LLM |
| **Shared objects** | Contacts, deals, goals |
| **Cross-domain** | Paperclip KPIs; forecasting |

---

## Domain: Agents / Orchestration

| Field | Evidence |
|-------|----------|
| **Ownership** | `revenue_os/agents/`, `runner_api_routers/agents.py`, `orchestration.py`, `go_to_market_orchestrator.py`, `orchestration_runtime.py` |
| **Responsibilities** | Agent registry, tasks, decisions, safeguards, GTM plan/run backends |
| **Inbound** | `/api/v1/agents/*`, `/api/v1/orchestration/*` |
| **Outbound** | Hermes/OpenClaw URLs (env); n8n trigger; DB agent tables |
| **Shared objects** | Agent registry/messages; orchestration logs |
| **Cross-domain** | Sales contact AI helpers; automation workflows |

---

## Domain: Automation & Heartbeat

| Field | Evidence |
|-------|----------|
| **Ownership** | `revenue_os/automation/`, `scheduler.py`, `tasks/`, routers `automation.py`, `heartbeat.py`, `n8n_webhooks.py` |
| **Responsibilities** | Workflow definitions/executions; recurring jobs; Celery tasks; n8n bridge |
| **Inbound** | `/api/v1/automation/*`, `/api/v1/heartbeat/*`, `/webhooks/n8n/*` |
| **Outbound** | Redis/Celery; DB; n8n HTTP |
| **Shared objects** | Workflow records, heartbeat runs, agent action log |
| **Cross-domain** | Lead scoring / Gmail sync jobs call sales/integrations services |

---

## Domain: Customer Success

| Field | Evidence |
|-------|----------|
| **Ownership** | `runner_api_routers/csm.py`, `revenue_os/customer_success/`, `src/csm_crew.py` |
| **Responsibilities** | Account health, at-risk, expansion, recommendations |
| **Inbound** | `/api/v1/csm/*` |
| **Outbound** | DB-derived health calculations |
| **Shared objects** | Account/deal/contact data |
| **Cross-domain** | Forecasting churn/expansion |

---

## Domain: Knowledge & Copilot

| Field | Evidence |
|-------|----------|
| **Ownership** | `knowledge_base` router; content KB models; `rag_service.py`, `search_service.py`, `copilot.py` |
| **Responsibilities** | KB CRUD, search, ask; copilot chat |
| **Inbound** | `/api/v1/knowledge-base/*`, `/api/v1/copilot/chat` |
| **Outbound** | ChromaDB; optional OpenAI |
| **Shared objects** | KB articles; embeddings store under `data/chroma_db` |
| **Cross-domain** | Activity log for copilot actions |

---

## Domain: Analytics / Reporting / Forecasting / Executive

| Field | Evidence |
|-------|----------|
| **Ownership** | `analytics.py`, `analytics_depth.py`, `reporting.py`, `forecasting.py`, `paperclip.py`, `revenue_os/analytics/`, `forecasting/`, `executive/`, `reporting/` |
| **Responsibilities** | Metrics/dashboards/reports; LTV/CAC/spend; ML-ish forecast endpoints; executive KPIs/insights |
| **Inbound** | Respective `/api/v1/*` and `/analytics` prefixes |
| **Outbound** | DB metric tables; compute modules |
| **Shared objects** | Analytics metric/data point records; marketing spend |
| **Cross-domain** | Heartbeat metric snapshots; CRM deals/contacts |

---

## Domain: Integrations & Messaging

| Field | Evidence |
|-------|----------|
| **Ownership** | `integrations.py`, `whatsapp.py`, `revenue_os/integrations/*` |
| **Responsibilities** | Email/Slack/calendar/Gmail/webhooks/WhatsApp connectors |
| **Inbound** | `/api/v1/integrations/*`, `/api/v1/whatsapp/*` |
| **Outbound** | External provider APIs |
| **Shared objects** | `ConnectorCredentialRecord` |
| **Cross-domain** | Marketing publish; heartbeat Gmail sync |

---

## Domain: Platform / Auth / Observability

| Field | Evidence |
|-------|----------|
| **Ownership** | `utils.py`, `middleware.py`, `metrics.py`, `revenue_os/auth.py`, `config.py`, `database.py`, `src/observability.py` |
| **Responsibilities** | API key/JWT auth, logging middleware, health/metrics, settings |
| **Inbound** | All HTTP apps |
| **Outbound** | Logs; Prometheus-ish metrics endpoints |
| **Shared objects** | Settings, engine/session, security schemes |
| **Cross-domain** | Used by every domain router |

---

## Domain: Frontend UX

| Field | Evidence |
|-------|----------|
| **Ownership** | `frontend/`, Jinja `templates/`, UI router |
| **Responsibilities** | HTML ops UI + React CRM |
| **Inbound** | Browser |
| **Outbound** | Calls API surfaces |
| **Shared objects** | API responses |
| **Cross-domain** | Surfaces multiple backend domains |
