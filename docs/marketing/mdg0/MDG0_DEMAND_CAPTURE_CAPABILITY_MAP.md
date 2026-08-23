# MDG0 — Demand Capture Capability Map

**Sprint:** MDG0  
**Date:** 2026-08-13  
**Mode:** AUDIT ONLY

## Canonical pre-Sales demand model

**NONE.**

There is no persisted Marketing Signal / InboundLead / VisitorConversion entity before Sales handoff.

The first durable “demand” artifact is **`QualifiedDemand`** at the Marketing→Sales boundary (MC04.5 FROZEN):

- Payload: `QualifiedDemandPayload` in `revenue_os/services/qualified_demand_service.py`
- Register: `POST /api/v1/marketing/qualified-demand/handoff`
- Persistence: `AgentActionLog` (`qualified_demand_handoff`)
- Sales accept creates `Contact` (SoT)

`ContactSource.WEB_FORM` exists on Contact but has **no Marketing form producer**.

Optional schema fields (`consent`, `content_attribution`, `marketing_qualification`) exist on the handoff payload — they are **not** populated by any public capture path.

## Capability map

| # | Capability | Class | Produces demand? |
|---|------------|-------|------------------|
| 1 | Human MC04 handoff API | API_ONLY | Yes (operator-typed) |
| 2 | Operator / Cockpit accept/reject of existing QD | LIVE (downstream) | No (consumes QD) |
| 3 | Optional attribution/consent JSON on handoff | PARTIAL schema | No capture |
| 4 | `WEB_FORM` ContactSource enum + score weight | DORMANT | No writer |
| 5 | `revenue_os/marketing/lead_nurturing.py` in-memory sketch | DORMANT | Unwired |
| 6 | CRM contact create / prospecting import | LIVE (Sales) | Bypasses Marketing demand |
| 7 | n8n email/meeting webhooks | PARTIAL | Post-CRM outreach; not audience→QD |
| 8 | Public web form / newsletter / demo / tracking | MISSING | — |

**Audience-origin LIVE demand producers: 0**  
**Demand-capture capabilities inspected: 8**

## What converts today

A human calling `POST /api/v1/marketing/qualified-demand/handoff` with `requested_by` human identity.

Content, SEO, website publish, and social do **not** create QualifiedDemand.
