# CP4 — Founder Operating Flow

**Sprint:** CP4  
**Date:** 2026-08-13

Required path (no DB writes, no service bypass, no spoofed cockpit `requested_by`, no agent mutation):

```
Demand → qualification → Sales acceptance → Contact status
  → Deal progression → closed_won → CommercialOutcome handoff
  → Revenue acceptance/rejection
```

## Classification

**FOUNDER OPERATING FLOW: PARTIAL**

## Step audit

| Step | API | Jinja / cockpit UI | Trusted operator (no client `requested_by`) |
|------|-----|--------------------|---------------------------------------------|
| Register QualifiedDemand | YES | NO | NO (client `requested_by`) |
| Sales accept | YES | YES (`/cockpit`) | YES (`FOUNDER_OS_OPERATOR_NAME`) |
| Sales reject | YES | NO | NO |
| Contact.status | YES | YES (score ≥ 70 only) | YES |
| Deal create | YES | NO (SPA UNMOUNTED) | N/A (create ungated) |
| Deal stage → closed_won | YES | NO | NO |
| CommercialOutcome handoff | YES | NO | NO |
| Revenue accept / reject | YES | NO | NO |

## Exact breaks (6)

1. QualifiedDemand **registration** — API only  
2. QualifiedDemand **reject** — API only (UI2.5 intentionally NOT EXPOSED)  
3. **Deal create** — not on Jinja shell  
4. **Deal stage progression** — not on any operator UI  
5. **CommercialOutcome handoff** — not on any operator UI  
6. **Revenue accept/reject** — not on any operator UI  

## What works today

A Founder with `FOUNDER_OS_OPERATOR_NAME` set can accept an already-registered demand and update a high-score Contact.status from `GET /cockpit`. Everything else requires curl + a client-supplied human `requested_by`.

## Cockpit honesty gap (not a new SoT)

`cockpit_read_model.py` still labels Revenue Outcome:  
`NOT YET ACTIVE — CommercialOutcome → Revenue intake not implemented`  

MC06.5 implemented the handoff/accept APIs. The panel text is **stale relative to backend**, frozen under UI2.5 (no cockpit redesign in MC06). This is a visibility defect, not a missing domain capability.
