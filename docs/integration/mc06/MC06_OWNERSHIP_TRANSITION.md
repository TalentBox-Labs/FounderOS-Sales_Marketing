# MC06 — Sales → Revenue Ownership Transition

**Sprint:** FOUNDER OS MC06  
**Date:** 2026-08-13

```
Sales owns Deal.stage (A3.5)
        ↓
eligible closed_won
        ↓
human Sales handoff  (AgentActionLog: commercial_outcome_handoff)
        ↓
human Revenue accept / reject
        ↓
Revenue owns CommercialOutcome representation (accepted audit row)
```

## Rules

- **No shared mutable SoT.** Deal remains Revenue entity SoT for CRM fields; Sales continues to operate stage via A3.5 only.
- Handoff payload is immutable after register (idempotent replay).
- Accept does not copy Deal into a second Deal store.
- Reject does not delete or alter Deal.
- Client / Project / Contact.status / invoices are out of scope.

## Prohibited

- Sales writing a Revenue financial record
- Revenue mutating Deal through this API
- Dual-write of the same mutable CommercialOutcome row by both OS
