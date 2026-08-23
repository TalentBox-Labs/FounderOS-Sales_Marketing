# CP4 — Product Maturity Matrix

**Sprint:** CP4  
**Date:** 2026-08-13

Rule: API existence alone is not OPERABLE. Operator usability required.

| # | Stage | Class | Why |
|---|-------|-------|-----|
| 1 | Audience Creation | **PARTIAL** | Website/static publish FROZEN; Social live BLOCKED; production domain OPEN (FDR-N05) |
| 2 | Demand Capture | **MISSING** | No form, webhook, or CTA→demand path |
| 3 | Demand Qualification | **PARTIAL** | Marketing handoff API; no UI; no automated qualification |
| 4 | Sales Intake | **PARTIAL** | Accept in cockpit; register + reject API-only |
| 5 | Contact / Lead Qualification | **OPERABLE** | A4.5 + cockpit status (high-score subset). Arbitrary contacts need API. |
| 6 | Company / Account Context | **PARTIAL** | Model + JWT CRUD; runner/UI missing |
| 7 | Deal Progression | **PARTIAL** | A3.5 API FROZEN; no Jinja/SPA stage control |
| 8 | Closed-Won Handling | **PARTIAL** | Stage write works; no UI; create-deal can skip FSM |
| 9 | CommercialOutcome Handoff | **PARTIAL** | MC06.5 FROZEN API; no UI |
| 10 | Revenue Acceptance | **PARTIAL** | Accept/reject API FROZEN; no UI |
| 11 | Revenue Operations | **MISSING** | Billing/recognition explicitly NOT_INCLUDED |
| 12 | Executive Visibility | **PARTIAL** | UI2.5 5 panels; CO still shown as NOT YET ACTIVE; 8/11 sources |
| 13 | Operator Actionability | **PARTIAL** | 2 cockpit mutations only |
| 14 | Governance / Auditability | **FROZEN** | Human gates, AgentActionLog, UI1.1, frozen contracts |

**Summary:** Architecture and auditability are ahead of product usefulness. The commercial backend is largely FROZEN; the Founder-facing operating loop is PARTIAL.
