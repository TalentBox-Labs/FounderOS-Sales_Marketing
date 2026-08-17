# SALES A2 — Implementation Sequence

**Sprint:** SALES A2  
**Date:** 2026-08-13  
**Rule:** Sequence only — no implementation in A2

---

## Proposed stages

| Sprint | Scope | Type | Notes |
|--------|-------|------|-------|
| **A3** | Runner Deal Stage Update (human-gated) | CONNECT_EXISTING | Selected — see ADR-006 |
| **A3.5** | Freeze A3 API/behavior baseline | Governance | After A3 green |
| **A4** | LeadScorer / Contact.status human gate | COMPLETE_EXISTING | Authority contract debt |
| **A4.5** | Freeze | Governance | |
| **A5** | Thin Companies on runner (C19 connect) **or** CommercialOutcome stub | CONNECT / BUILD | Choose by evidence post A3–A4 |
| **A5.5** | Freeze | Governance | |
| **A6** | CRM SPA refactor+mount prep (still RETAIN_AND_REFACTOR) | UI | Only after stage API proven |
| Later | QualifiedDemand emitter/intake; n8n ops enablement | BUILD / ops | Not before pipeline ops solid |

Do **not** expand into enormous roadmap. Later slices require fresh A2-style evidence if priorities shift.

---

## Explicit non-sequence (now)

- Mount CRM without refactor ADR  
- HubSpot/Salesforce  
- Autonomous selling agents  
- Relational PipelineStage migration  
- `sales_os` package extraction as first feature  
