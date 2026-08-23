# MC06 — Known Limitations

**Sprint:** FOUNDER OS MC06  
**Date:** 2026-08-13

| Limitation | Classification |
|------------|----------------|
| `closed_lost` not eligible | DEFERRED (v1 closed_won only) |
| No Revenue intake (Client/CUSTOMER/CS) | OUT_OF_SCOPE |
| No billing / recognition | OUT_OF_SCOPE |
| No cockpit / CRM UI | OUT_OF_SCOPE (UI2.5 unchanged) |
| A3.5 still reports `commercial_outcome_emitted: false` | INTENTIONAL — frozen contract |
| EventBus history is in-memory | ACCEPTED_LEGACY (MC04 same) |
| `AgentActionLog` has no unique DB constraint | Application-level idempotency (MC04 same) |
| Value snapshot is not authoritative | INTENTIONAL (FAILURE H) |
| JWT `PUT /api/v1/deals/{id}` close path still ungated | ACCEPTED_LEGACY (A3.5) — not MC06 SoT |
