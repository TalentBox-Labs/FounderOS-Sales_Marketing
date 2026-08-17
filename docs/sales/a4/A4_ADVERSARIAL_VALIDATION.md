# A4 — Adversarial Validation

**Sprint:** SALES A4  
**Date:** 2026-08-13  
**Result:** PASS

## Attack vectors tested

| Vector | Result |
|--------|--------|
| Agent requester (`agent`) | **BLOCKED** 403 |
| AI requester (`ai:copilot`) | **BLOCKED** 403 |
| Automation requester (`bot`) | **BLOCKED** 403 |
| Missing API key (when configured) | **BLOCKED** 401 |
| Malformed contact ID | **BLOCKED** 422 |
| Nonexistent contact | **BLOCKED** 404 |
| Invalid status enum | **BLOCKED** 422 |
| High score via POST /score | **NO status mutation** |
| Hermes planner qualify action | **NO status mutation** (recommendation only) |
| Celery enrich_lead | **NO auto-promotion** |

## Non-human mutation via LeadScorer path

**FAIL if any pass** — none observed.

## Residual paths (documented, out of A4 slice)

| Path | Notes |
|------|-------|
| JWT `PUT /api/v1/contacts/{id}` | Pre-existing ungated API — not LeadScorer path |
| n8n `meeting.booked` webhook | External event path — deferred |
| CRM create contact initial status | Human API create — not qualification promotion |

No successful non-human mutation via A4 LeadScorer/score flow.
