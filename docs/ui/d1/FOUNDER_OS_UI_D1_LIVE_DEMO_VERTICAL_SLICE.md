# Founder OS UI-D1 — Live Demo Vertical Slice

**Sprint:** UI-D1  
**Branch:** ui-d1  
**Baseline:** 1e446ac  
**Status:** IMPLEMENTED

## Objective

Deliver a browser-only founder revenue demo using incremental Jinja modernization on existing FastAPI APIs — no new SoT, no new frontend framework, no booking (M4 boundary).

## Primary surfaces

| # | Surface | Route |
|---|---------|-------|
| 1 | Login | `/login` |
| 2 | Founder Command Center | `/command` |
| 3 | Demand & Contacts | `/demand` |
| 4 | Contact Revenue Workspace | `/contacts/{id}` |
| 5 | Approval Inbox | `/pending-approvals` |
| 6 | Reply / Next Action | Contact workspace panel |
| 7 | Activity / Provenance | `/activity` |

Revenue workflow mutations remain on `/operator` (OF1.5 frozen) — linked, not duplicated.

## Cockpit fix

`templates/cockpit.html:53` — Jinja dict `.items` method collision fixed via bracket access `data['items']`.

## Booking boundary

UI displays meeting interest and booking eligibility only. Scheduling/booking is **CROSS_STREAM_DEPENDENCY: M4 booking contract required**.
