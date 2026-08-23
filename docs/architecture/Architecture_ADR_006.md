# Architecture ADR-006 — Sales A3 First Implementation Slice Selection

**ADR ID:** Architecture_ADR_006  
**Status:** Accepted (selection only — **no implementation in A2**)  
**Sprint:** SALES A2 — Capability & Implementation Priority Review  
**Date:** 2026-08-13  

**Decision type:** Implementation priority selection  
**Implementation changes in this ADR:** **NONE** (A3 executes later)

Does **not** modify Architecture v2.2 or Sales OS Architecture Baseline v1.0 contracts. Implements *against* A1.5 freeze.

Related: [SALES_A2_PRIORITY_SCORECARD.md](../sales/SALES_A2_PRIORITY_SCORECARD.md), [SALES_A1_5_BASELINE_MANIFEST.md](../sales/SALES_A1_5_BASELINE_MANIFEST.md)

---

## Context

Sales OS baseline is FROZEN (A1.5). Founder needs the highest-value next **bounded** implementation slice. A0/A1 identified runner CRM missing deal stage update while JWT/`advance_deal_stage` already exist.

---

## Candidates (top 3)

| Rank | Candidate | Score |
|------|-----------|------:|
| 1 | Runner Deal Stage Update | 4.85 |
| 2 | Marketing→Sales QualifiedDemand | 3.38 |
| 3 | Outreach send n8n completion | 3.33 |

---

## Decision

**Select A3 = Runner Deal Stage Update** (CONNECT_EXISTING).

Bounded slice:

- Add human-requester-gated deal stage update on **runner** `/api/v1/crm/deals/{id}` (PATCH or PUT stage)  
- Reuse `revenue_os.services.deal_automation_service.advance_deal_stage`  
- Persist via existing Revenue `Deal` SoT  
- Focused tests for stage transitions + human gate  
- **Complexity: S**

### Explicit exclusions (A3)

- No CRM SPA mount/refactor  
- No Marketing QualifiedDemand  
- No CommercialOutcome / Client auto-create  
- No n8n/Proxycurl activation  
- No schema migration / new tables  
- No agent autonomous stage changes  
- No JWT stack deletion  

---

## Why winner won

Highest weighted score; closes largest workflow break; maximum reuse; zero new external deps; fits Sales pipeline **ops** / Revenue entity SoT; margin **1.47** over #2.

## Why #2 lost

BUILD_NEW + Marketing coordination; manual capture already works; lower reuse.

## Why #3 lost

External n8n dependency; approvals already LIVE; ops enablement ≠ Sales domain unlock.

---

## Dependencies

| Dep | Status |
|-----|--------|
| Marketing | None for A3 |
| Revenue | Soft — mutate Deal via existing service (SoT unchanged ownership) |
| Agent | None — HUMAN_ONLY stage |
| External | None required |
| CRM UI | Not required |

## Risks

Incorrect stage / premature closed_won without handoff event — mitigate with human requester + audit; defer CommercialOutcome to later sprint.

## Conditions that reopen decision

- Founder mandates Marketing intake before pipeline ops  
- Evidence that runner is deprecated as CRM facade  
- Security finding that stage mutation must wait for LeadScorer gate (then swap A3↔A4)

---

## Recommended next sprint

**SALES A3 — RUNNER DEAL STAGE UPDATE (HUMAN-GATED)**
