# MDG0 — Audience → Demand Gap

**Sprint:** MDG0  
**Date:** 2026-08-13  
**Mode:** AUDIT ONLY

## Target chain

```
CONTENT / AUDIENCE
       ↓
ATTENTION
       ↓
INTENT
       ↓
DEMAND CAPTURE
       ↓
QUALIFICATION INPUT
       ↓
QUALIFIEDDEMAND
       ↓
FROZEN OF1.5 OPERATOR FLOW (COMPLETE)
```

## Edge classification

| Edge | Status | Evidence |
|------|--------|----------|
| Audience → Attention | **PARTIAL** | Static site + RSS reachable; social blocked; SEO prod indexing blocked (FDR-N05) |
| Attention → Intent | **MISSING** | No interactive CTA / form / signup UX |
| Intent → Demand capture | **MISSING** | No form handler, conversion event, or pre-Sales demand store |
| Demand capture → Qualification input | **MISSING** | No MQL engine; `marketing_qualification` is optional handoff JSON only |
| Qualification → QualifiedDemand | **PARTIAL** | Human-only MC04.5 register API |
| QualifiedDemand → Operator Flow | **CONNECTED** | OF1.5 FROZEN: Demand→Revenue COMPLETE |

## First missing capability

**Inbound conversion capture** that creates an attributable Marketing demand record (or directly a controlled QualifiedDemand registration) from untrusted public input.

Until that exists, Audience → Demand remains the first material value-chain break.

## Overall state

**Audience → Demand: MISSING**

Bounded Demand → Revenue Decision remains COMPLETE (OF1.5). Total Founder OS value chain remains PARTIAL.
