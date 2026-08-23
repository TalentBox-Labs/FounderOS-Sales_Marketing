# UI1 — Founder Action & Authority Matrix

**Sprint:** UI1  
**Date:** 2026-08-13

## Action taxonomy

| Action | Class | Authority | API / Surface | Cockpit expose? |
|--------|-------|-----------|---------------|-----------------|
| View SEO readiness | OBSERVE | READ_ONLY | GET `/seo`, `/api/v1/seo/*` | **YES** |
| View Technical SEO | OBSERVE | READ_ONLY | `/seo/technical` | **YES** |
| View contacts/deals | OBSERVE | READ_ONLY | GET `/api/v1/crm/*` | **YES** |
| View lead score | REVIEW | READ_ONLY | POST `.../score` (no status change) | **YES** |
| View score recommendation | REVIEW | READ_ONLY | score response `suggested_status` | **YES** |
| Change Contact.status | EXECUTE | **HUMAN_ONLY** | PATCH `.../contacts/{id}/status` | **YES** (with `requested_by`) |
| Advance deal stage | EXECUTE | **HUMAN_ONLY** | PATCH `.../deals/{id}/stage` | **YES** (with `requested_by`) |
| Register QualifiedDemand | EXECUTE | **HUMAN_ONLY** | POST `.../marketing/qualified-demand/handoff` | **YES** |
| Accept/reject handoff | DECIDE | **HUMAN_ONLY** | POST `.../sales/intake/demand/*` | **YES** |
| Editorial approve/reject | APPROVE | **HUMAN_ONLY** | `/api/v1/editorial/*` | Link to existing UI |
| Publishing promote | APPROVE | **HUMAN_ONLY** | publishing engine | Link to `/publishing` |
| Agent score-only | — | AGENT_ALLOWED | Hermes score paths (no status) | No mutation UI |
| Agent qualify contact | — | **NOT_IMPLEMENTED** (blocked A4.5) | — | Must not expose |
| Create contact (CRM POST) | EXECUTE | API key only | POST `/crm/contacts` | Defer UI2 — ungated create |
| JWT contact status PUT | EXECUTE | **Ungated bypass** | `revenue_os/api/v1/contacts` | **Do not expose** |

## Human-only count

**6** primary human-gated mutation families: Contact.status, Deal.stage, MC04 handoff, MC04 accept, MC04 reject, Editorial approve (plus publishing human publish).

## Safe UI2 candidates

1. Read-only Executive Cockpit home (queues + snapshots)
2. QualifiedDemand review queue (read handoff audit + accept/reject with human name)
3. Optional: deal stage / contact status action panel reusing frozen PATCH contracts

**Do not weaken HUMAN_ONLY boundaries.**
