# UI1 — Cockpit Data Source Map

**Sprint:** UI1  
**Date:** 2026-08-13

| Widget | Authoritative source | Existing API | Aggregation needed? | SoT risk |
|--------|---------------------|--------------|---------------------|----------|
| SEO readiness summary | `seo_engine` | GET `/api/v1/seo/readiness/summary` | No | **Low** |
| Technical SEO summary | `seo_engine` | GET `/api/v1/seo/technical/summary` | No | **Low** |
| Contact count by status | Revenue `Contact` | GET `/api/v1/crm/contacts` | Client-side group OK | **Low** if read-only |
| Deal pipeline by stage | Revenue `Deal` | GET `/api/v1/crm/deals` | Client-side group OK | **Low** |
| Lead score bands | Contact.lead_score | Hermes or CRM | Optional server aggregate | **Low** |
| Pending editorial | Editorial engine | GET `/api/v1/editorial/pending` | No | **Low** |
| Publishing queue | Publishing engine | GET publishing routes | No | **Low** |
| QualifiedDemand queue | AgentActionLog | **None** | **Yes** — read-only `/api/v1/ops/qualified-demand/pending` proposed | **Low** if audit read |
| Heartbeat health | HeartbeatRun | GET `/api/v1/heartbeat/status` | No | **Low** |
| Agent activity | AgentActionLog | GET heartbeat activity | No | **Low** |
| Commercial flow diagram | Multiple | Compose from above | Read-only derive | **Low** |
| Frozen baseline status | Docs | Static JSON manifest optional | No runtime SoT | **None** |

**Pattern:** existing authoritative APIs → optional read-only aggregation → Jinja/React render.

**Avoid:** cockpit DB tables, duplicated Contact/Deal state, frontend-derived canonical mutations.

**Cockpit Can Remain Read-Model Only:** **YES** (mutations optional via existing human-gated endpoints only).

**New Shared SoT Required:** **NO**

**Database Migration Required for UI2:** **NO**

**External Integration Required for UI2:** **NO**
