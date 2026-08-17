# CP4 — Marketing Demand Gap

**Sprint:** CP4  
**Date:** 2026-08-13

## Question

Does Founder OS convert audience activity into a canonical demand object?

**NO.**

## What exists

| Mechanism | State |
|-----------|-------|
| Website / static publish | FROZEN (Marketing) |
| SEO readiness / technical SEO | FROZEN engines; production activation BLOCKED (FDR-N05) |
| Social live | BLOCKED (FD-01, ES-01..03, adapter `NOT_IMPLEMENTED`) |
| `ContactSource.WEB_FORM` | Enum + scorer weight only |
| MC04 handoff `source=web_form` | Mapping only; no producer |
| `content_attribution` / UTM | Optional JSON on handoff payload; **no HTTP capture** |
| Website `<form>` / Turnstile | **Absent** |
| n8n → QualifiedDemand | **Absent** |

## What converts today

**Human curl** of `POST /api/v1/marketing/qualified-demand/handoff`.

Content, SEO, and (future) social do **not** create QualifiedDemand.

## Implication

Audience → Demand remains the **first material value-chain break**.

A demand-generation sprint is commercially important but **CONDITIONAL** (public surface, spam/abuse, domain). It should not precede making the already-frozen commercial path Founder-operable, or demand will still die in API-only intake.
