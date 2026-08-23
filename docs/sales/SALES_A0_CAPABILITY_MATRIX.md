# SALES A0 — Capability Matrix

**Sprint:** SALES A0  
**Date:** 2026-08-13  
**Rule:** Exactly one class per capability. Repository/runtime evidence wins over docs.

Classes: `LIVE` · `PARTIAL` · `API_ONLY` · `UI_ONLY` · `PLACEHOLDER` · `DEAD_CODE` · `NOT_IMPLEMENTED`

---

## Matrix

| ID | Capability | Class | Primary evidence |
|----|------------|-------|------------------|
| C01 | Jinja prospecting shell `/sales` | **LIVE** | `templates/sales.html`; `ui.py`; nav in `base.html`; HTTP 200 |
| C02 | Prospecting plan / import APIs | **LIVE** | `runner_api_routers/prospecting.py`; `lead_prospecting_service.py` |
| C03 | Contacts list/create/get (runner CRM) | **LIVE** | `runner_api_routers/crm.py` `/contacts` |
| C04 | Contact enrich endpoint | **PARTIAL** | CRM enrich route; Proxycurl config often missing |
| C05 | Deals list/create/get (runner CRM) | **PARTIAL** | Create/list/get; **no PUT/PATCH stage** on runner |
| C06 | Pipeline summary (runner) | **PARTIAL** | `GET /api/v1/crm/pipeline` aggregate only |
| C07 | Activities create/list/complete | **LIVE** | CRM activities + `Activity` model |
| C08 | Follow-ups inbox | **LIVE** | `GET /api/v1/crm/followups`; `followups.py` |
| C09 | Outreach sequences CRUD | **LIVE** | `runner_api_routers/outreach.py` + model |
| C10 | Outreach send execution | **PARTIAL** | Approvals → n8n `send-email`; n8n CONFIGURATION REQUIRED |
| C11 | Sales AI assists (research/email/LI opener/sequence) | **LIVE** | `/api/v1/agents/sales/{id}/*`; `sales_agents.py` |
| C12 | Hermes score / qualify / pipeline health | **LIVE** | `runner_api_routers/hermes.py` + scorers |
| C13 | Approvals queue (outreach/deal propose) | **LIVE** | `approvals.py` service + router |
| C14 | Copilot operator assist | **LIVE** | `copilot.py` + SPA page (when `/app` built) |
| C15 | Goals / Hermes goals | **LIVE** | goals router + models |
| C16 | Automation / workflow engine surfaces | **PARTIAL** | EventBus/WorkflowEngine; much in-memory |
| C17 | CSM account health APIs | **LIVE** | `csm.py`; health over Company |
| C18 | React CRM SPA `/app` | **PARTIAL** | `frontend/` source; `dist` absent → 503 |
| C19 | Companies CRUD | **API_ONLY** | `revenue_os/api/v1/companies.py` on JWT app only |
| C20 | Deal stage advance | **API_ONLY** | Revenue OS JWT deals PUT; not on runner CRM |
| C21 | Forecasting / win probability APIs | **API_ONLY** | `forecasting` router; no Jinja sales UI |
| C22 | JWT dual CRM stack (`revenue_os.main`) | **PARTIAL** | Full CRUD exists; not primary runner mount |
| C23 | Revenue OS static frontend fallback | **PLACEHOLDER** | `{"message": "frontend not built"}` pattern |
| C24 | MeetingActivity persistence writers | **DEAD_CODE** | Schema only; no writers found |
| C25 | Marketing lead nurturing (`SubscriberProfile`) | **DEAD_CODE** | In-memory; not CRM-wired |
| C26 | Named Opportunity entity | **NOT_IMPLEMENTED** | Deal used instead |
| C27 | Marketing → Sales lead handoff | **NOT_IMPLEMENTED** | `WEB_FORM` enum only |
| C28 | Closed-won → Client/CSM handoff | **NOT_IMPLEMENTED** | No auto Client/Project; no auto CUSTOMER |

---

## Counts

| Class | Count |
|-------|------:|
| LIVE | 12 |
| PARTIAL | 6 |
| API_ONLY | 4 |
| UI_ONLY | 0 |
| PLACEHOLDER | 1 |
| DEAD_CODE | 2 |
| NOT_IMPLEMENTED | 3* |
| **Total in matrix** | **28** |

\*Matrix lists 3 explicit NOT_IMPLEMENTED rows; **Missing Core Capabilities** in the recommendation expands to **9** product gaps (boundary package, stage entity, owner RBAC, companies UI, runner stage updates, etc.) — see `SALES_A0_RECOMMENDATION.md`.

### Missing core (expanded)

1. Discrete `sales_os` package / ownership ADR  
2. Lead entity clarity (Lead vs Contact.status)  
3. Opportunity naming ADR (or Deal=Opportunity)  
4. Marketing→Sales handoff  
5. Runner CRM deal stage update  
6. Close→Customer/Client handoff  
7. Owner FK / role boundaries  
8. Companies UI in operator shell  
9. Relational PipelineStage model  

**Missing Core Capabilities: 9**

---

## React CRM `/app` disposition

| Question | Answer |
|----------|--------|
| Source exists? | YES — `frontend/` (`workcrew-crm-frontend`) |
| Builds? | Build path exists (`npm run build`); **not built** in this workspace |
| `frontend/dist`? | **NO** |
| Mounted? | Conditionally; currently **503** |
| APIs expected? | Runner `/api/v1/crm/*`, agents, csm, hermes, approvals, … |
| Backend? | `runner_api` (not `revenue_os.main`) |
| Reusable? | **YES** |
| Abandoned? | **NO** — Docker still builds dist |

**Existing CRM UI: UNMOUNTED**
