# MC04 — Capability Map (NOVA)

**Sprint:** FOUNDER OS MC04  
**Date:** 2026-08-13  
**Implementation Type:** **BUILD_NEW** (contract existed; runtime absent)

## Reused components

| Component | Classification | Reuse |
|-----------|----------------|-------|
| Revenue `Contact` / `Company` | LIVE | Canonical SoT for intake |
| `ContactSource.WEB_FORM` | LIVE | Source mapping |
| `AgentActionLog` | LIVE | Handoff + intake audit + idempotency |
| `EventBus` | LIVE | Handoff/accept/reject events |
| `is_human_approver` | LIVE | A3/A4 authority pattern |
| `_verify_api_key` | LIVE | Runner auth |
| Runner CRM create pattern | LIVE | Reference only — intake uses service |

## Built (MC04)

| Artifact | Role |
|----------|------|
| `qualified_demand_service.py` | Payload validation, handoff register, accept/reject |
| `qualified_demand.py` router | Marketing handoff + Sales intake endpoints |

## Not reused (explicit)

| Item | Reason |
|------|--------|
| LeadScorer auto-qualify | A4.5 prohibits |
| Deal automation | Not in contract |
| `lead_nurturing` in-memory | Not wired; not CRM SoT |
| Direct Marketing CRM writes | Prohibited |
