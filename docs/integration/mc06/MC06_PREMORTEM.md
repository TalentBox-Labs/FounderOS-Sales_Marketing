# MC06 — Pre-Mortem (Failure Modes)

**Sprint:** FOUNDER OS MC06  
**Date:** 2026-08-13

| ID | Failure | Prevention |
|----|---------|------------|
| A | closed_won silently creates Revenue state | A3.5 unchanged; separate handoff + accept |
| B | Retry creates duplicates | `outcome_id` idempotency + one open handoff per Deal |
| C | Shared mutable SoT | Audit rows only; Deal not dual-owned |
| D | Agent/AI impersonates human | Router 403 + service `HumanAuthorityError` |
| E | Revenue accept mutates Deal | Accept writes `AgentActionLog` only |
| F | Grows into billing/accounting | Explicit `recognized_revenue: false`; no Client/invoice |
| G | Frozen contract violation | A3.5/A4.5/MC04.5/A1.5 files not rewritten |
| H | Reports non-authoritative finance as truth | `value_authoritative: false` on snapshots |
