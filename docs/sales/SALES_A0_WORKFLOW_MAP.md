# SALES A0 — Workflow Map (HERMES)

**Sprint:** SALES A0  
**Date:** 2026-08-13  
**Mode:** AUDIT ONLY

---

## Funnel

`lead capture → qualification → contact → opportunity → pipeline → close → handoff`

---

## Stage map

| Stage | Coverage | Classification | Evidence |
|-------|----------|----------------|----------|
| Lead capture | Partial | PARTIAL | CRM contact create; prospecting import; webhook surfaces; `WEB_FORM` unused |
| Qualification | Strong | LIVE / PARTIAL | Hermes scoring; LeadScorer status auto-update; dual scorer conflict |
| Contact | Strong | LIVE | Contact is the person record throughout |
| Opportunity | Partial | PARTIAL | Deal create; no Opportunity entity |
| Pipeline | Partial | PARTIAL | Default pipeline; summary API; stage advance weak on runner/UI |
| Close | Weak | PARTIAL | CLOSED_WON on JWT path; CRM UI cannot close |
| Handoff | Thin | NOT_IMPLEMENTED | CSM health read-only; no Client auto-create |

**Sales Workflow Coverage: ~45%**

Weighted: capture/qualify/contact stronger; stage movement, close, handoff weaker.

---

## Workflow types

| Workflow | Type |
|----------|------|
| Prospecting plan → UI | Implemented (Jinja + API) |
| Contact CRUD runner | Implemented (API; SPA when built) |
| Deal create runner | Implemented |
| Deal stage move runner UI | Missing |
| Deal stage move JWT API | API-only |
| Auto deal from qualify | Partial (Hermes/planner/approvals) |
| Outreach propose → approve → n8n | Partial |
| Marketing nurture → CRM | Dead / not wired |
| Marketing publish → lead | Missing |
| Closed-won → delivery Client | Missing |

---

## Marketing → Sales (observe only)

Potential future handoff points (not implemented):

1. `ContactSource.WEB_FORM`  
2. `LEAD_CREATED` / new-lead webhook  
3. `lead_nurturing.SubscriberProfile` (parallel, unwired)  
4. Analytics funnel narrative only  

**Do not implement in A0.**

---

## Sales Workflow Coverage

**45%**
