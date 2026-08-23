# A4 — Runner Integration Plan (HERMES)

**Sprint:** SALES A4  
**Date:** 2026-08-13

## Architecture

```
Founder OS Runner (crm router)
  → POST /contacts/{id}/score     (autonomous — score only)
  → PATCH /contacts/{id}/status   (human gate)
      → is_human_approver(requested_by)
      → apply_contact_status_update
      → EventBus CONTACT_STATUS_CHANGED
```

Hermes `/score-contacts` continues to call `score_contacts_batch` — now score-only.

## Rules

- Runner contains **no** scoring business logic
- Scoring delegated to `LeadScorer.calculate_score` in service layer
- Status mutation only via human-gated PATCH
