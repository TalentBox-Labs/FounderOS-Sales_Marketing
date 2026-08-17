# QUALIFIED DEMAND HANDOFF CONTRACT v1

**Sprint:** FOUNDER OS MC04  
**Date:** 2026-08-13  
**Authority:** Implements frozen `SALES_MARKETING_CONTRACT` / boundary v1.0

## Payload (minimum)

| Field | Required | Owner before handoff |
|-------|----------|-------------------|
| `demand_id` | Yes | Marketing (idempotency key) |
| `occurred_at` | Yes | Marketing |
| `source` | Yes | Marketing |
| `channel` | No | Marketing |
| `person.email` | Yes | Marketing |
| `person.name` | No | Marketing |
| `person.phone` | No | Marketing |
| `person.linkedin_url` | No | Marketing |
| `company_hint` | No | Marketing |
| `marketing_qualification` | No | Marketing (immutable after handoff) |
| `consent` | No | Marketing |
| `content_attribution` | No | Marketing |

## Transport (v1)

| Step | Endpoint | Actor |
|------|----------|-------|
| Marketing handoff | `POST /api/v1/marketing/qualified-demand/handoff` | Human Marketing operator |
| Sales accept | `POST /api/v1/sales/intake/demand/accept` | Human Sales operator |
| Sales reject | `POST /api/v1/sales/intake/demand/reject` | Human Sales operator |

## Ownership

| Phase | Marketing | Sales |
|-------|-----------|-------|
| Before handoff | Qualification + attribution | — |
| After handoff register | Payload immutable in audit | — |
| After Sales accept | Read-only attribution in Contact.notes | Contact SoT |
| After Sales reject | Unchanged | Audit only |

## Behaviors

| Case | Behavior |
|------|----------|
| Duplicate `demand_id` handoff | Idempotent 200 |
| Duplicate `demand_id` accept | Idempotent 200, same `contact_id` |
| Duplicate email accept | Merge — link existing Contact |
| Reject | Audit only, no Contact |
| Accept after reject | 422 if not accepted yet; reject blocked after accept |
| Auto Contact.status | **NO** — status `LEAD` |
| Auto Deal | **NO** |

## Error semantics

| Code | Condition |
|------|-----------|
| 403 | Agent/AI requester |
| 422 | Invalid payload, missing handoff, already accepted on reject |
