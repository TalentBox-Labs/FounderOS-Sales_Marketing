# UI1 — Capability → Operating Surface Matrix

**Sprint:** UI1  
**Date:** 2026-08-13

| Capability | OS | SoT | Backend | API | UI | UI State | Mutation | Authority | Audit | Cockpit | Reuse |
|------------|-----|-----|---------|-----|-----|----------|----------|-----------|-------|---------|-------|
| SEO Readiness | Mkt | seo_engine | `src/tools/seo_engine/` | `/api/v1/seo/*` | `/seo` Jinja | LIVE_MOUNTED | Read | API key | Engine report | **High** | Jinja SEO pages |
| Technical SEO | Mkt | seo_engine | same | same | `/seo/technical` | LIVE_MOUNTED | Read | API key | same | **High** | same |
| Editorial approval | Mkt | editorial | `editorial.py` | `/api/v1/editorial/*` | `/editorial/*` | LIVE_MOUNTED | Human approve | HUMAN_ONLY | JSONL | **High** | editorial UI |
| Publishing queue | Mkt | publishing | `publishing.py` | `/api/v1/publishing/*` | `/publishing` | LIVE_MOUNTED | Human publish | HUMAN_ONLY | job audit | Med | publishing UI |
| Social Engine | Mkt | — | NOT_IMPLEMENTED | — | — | **MISSING** | — | — | S0 docs | Low | Parked |
| QualifiedDemand handoff | Cross | audit+Contact | `qualified_demand_service.py` | MC04 routes | **NONE** | API_ONLY | Human handoff/accept | HUMAN_ONLY | AgentActionLog | **High** | New UI2 forms |
| Lead scoring | Sales | Contact.lead_score | `lead_scoring_service.py` | `/crm/contacts/{id}/score` | React read | UNMOUNTED/PARTIAL | Score only | Autonomous OK | LEAD_SCORED | **High** | API |
| Contact.status | Sales | Contact | A4.5 service | `PATCH /crm/contacts/{id}/status` | **NONE** | API_ONLY | Human | HUMAN_ONLY | EventBus | **High** | UI2 gate form |
| Deal stage | Sales | Deal | A3.5 service | `PATCH /crm/deals/{id}/stage` | **NONE** | API_ONLY | Human | HUMAN_ONLY | EventBus | **High** | UI2 gate form |
| CRM contacts/deals | Sales | Revenue models | `crm.py` | `/api/v1/crm/*` | React + `/sales` | PARTIAL | Create (ungated) | API key | partial | Med | React when mounted |
| Prospecting | Sales | — | `prospecting.py` | `/api/v1/prospecting/*` | `/sales` Jinja | LIVE_MOUNTED | Import | API key | partial | Med | sales.html |
| CommercialOutcome | Rev | — | NOT_IMPLEMENTED | — | — | **MISSING** | — | Future | — | Low | Deferred |
| System health | Ops | heartbeat | `heartbeat.py` | `/api/v1/heartbeat/*` | Dashboard partial | PARTIAL | Read | API key | AgentActionLog | **High** | heartbeat API |
| Frozen baselines | Gov | docs | — | — | **NONE** | DOC_ONLY | — | — | — | Med | Static manifest read |
| Content studio | Mkt | content | `content_studio.py` | API | Jinja 3 routes | LIVE_MOUNTED | Workflow | API key | partial | Med | existing pages |

**Legend:** Mkt=Marketing, Rev=Revenue. Runtime verified — not inferred from docs alone.
