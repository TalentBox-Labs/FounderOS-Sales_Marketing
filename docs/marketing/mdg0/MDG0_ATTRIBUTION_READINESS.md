# MDG0 — Attribution Readiness

**Sprint:** MDG0  
**Date:** 2026-08-13  
**Mode:** AUDIT ONLY

## Overall

**PARTIAL** (handoff schema) / **MISSING** (audience capture).

## Field readiness

| Field | Status | Evidence |
|-------|--------|----------|
| Content source / content_id | PARTIAL | Optional `content_attribution` on `QualifiedDemandPayload`; no auto-bind from publish |
| Page / landing path | PARTIAL | Contract narrative; no middleware capture |
| CTA id | MISSING | No CTA component IDs in public site |
| Referrer | MISSING | No referrer ingest |
| UTM source / medium / campaign | PARTIAL | Appear in MC04 tests as example JSON; no HTTP UTM parser |
| Social source | MISSING | Social not live; no social attribution pipeline |
| Organic source | PARTIAL | Local SEO engines; GSC/organic click capture not wired |
| Timestamp | PARTIAL | `occurred_at` required on handoff; not from visitor session |
| User-provided identity | PARTIAL | Required `person.email` on handoff; no form source |
| Consent | PARTIAL | Optional `consent` dict; no consent UX / policy enforcement |

## Rule

Do not invent attribution infrastructure in MDG1 beyond fields already accepted by the frozen MC04.5 payload unless a new ADR expands the contract.
