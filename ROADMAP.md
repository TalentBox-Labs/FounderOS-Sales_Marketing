# WorkCrew AI Founder OS — Architecture Audit & Roadmap

Audit date: 2026-08-04 · Branch: `claude/sharp-davinci-3mbch4`

## 1. Architecture audit (what exists)

**Stack**: FastAPI (`runner_api.py`, 25+ routers in `runner_api_routers/`) ·
SQLAlchemy 2 / PostgreSQL-or-SQLite (`revenue_os/models/`, tables auto-created
on startup) · React 18 + Vite SPA (`frontend/`, hash routing, served at `/app`)
· CrewAI crews (`src/`) · asyncio heartbeat scheduler (`revenue_os/scheduler.py`).

**Conventions**: routers are thin, logic lives in `revenue_os/services/`;
API-key bearer auth via `_verify_api_key`; every autonomous action goes through
`activity_log.log_agent_action`; events flow through `revenue_os/automation/events.EventBus`;
risky actions file into the approvals queue; n8n is the outbound automation arm
(bridge + inbound webhooks at `/webhooks/n8n`).

## 2. Module status vs. the Founder OS vision

| Vision module | Status | What exists |
|---|---|---|
| Dashboard | 🟡 partial | Stats, system status, goals. Missing: AI suggestions, follow-ups, tasks |
| Sales CRM | 🟡 partial | Contacts/deals CRUD + scoring + pipeline. Missing: companies UI, activities/notes/tasks timeline |
| Marketing OS | 🟡 partial | WhatsApp console, content crews, AEO/GEO strategy docs. Missing: SEO/GEO *tracking*, SEM, social calendar, email-sequence REST+UI |
| AI Content Studio | 🟡 backend | CMS pipeline + crews exist (Jinja UI at `/`). Not in React app |
| Workflow Automation | 🟡 partial | Event→action engine, presets, n8n loop. Missing: visual builder |
| Multi-Agent System | 🟡 partial | Hermes planner (goal→plan→execute), CrewAI crews, orchestration scaffolding. Missing: agent registry/status, inter-agent tasks |
| **Founder Copilot** | 🔴 missing | — |
| Analytics | 🟡 partial | Persisted time-series + charts. Missing: attribution, funnels, CAC/LTV |
| Knowledge Base | 🔴 missing | chromadb dependency present, nothing wired |
| Integrations layer | 🟡 partial | n8n, WhatsApp, Hashnode/LinkedIn publishers. No unified abstraction |

Foundations already in place that the vision requires: durable audit trail,
heartbeat (proactive loop), approvals (human-in-the-loop), goal planner,
closed n8n loop, auth, single-container deploy.

## 3. Milestones (build order)

1. **M1 — Founder Copilot (this milestone)**: one chat interface that answers
   "what needs follow-up / today's priorities / show pipeline" and *executes*
   (create goals, run scoring, surface approvals) through existing services.
   Deterministic intent router now; LLM slot-in later without API changes.
2. **M2 — CRM depth**: activities/notes/tasks + timeline per contact/deal,
   follow-up engine feeding Dashboard + Copilot.
3. **M3 — Marketing OS core**: email-sequence REST + UI, SEO/GEO tracking
   models (keywords, rankings, AI-visibility checks) with scores on Dashboard.
4. **M4 — Visual workflow builder** on the existing event→action engine.
5. **M5 — Agent registry & collaboration**: agent status page, inter-agent
   task handoff, per-agent memory/goals/permissions.
6. **M6 — Knowledge base + RAG** (chromadb; notes, playbooks, semantic search).
7. **M7 — Integrations abstraction** (connector registry, credentials vault).
8. **M8 — Analytics depth**: attribution, funnel, CAC/LTV, agent productivity.

Each milestone ships: DB changes (auto-created), services, API, React page(s),
audit-trail integration, browser-verified, committed.
