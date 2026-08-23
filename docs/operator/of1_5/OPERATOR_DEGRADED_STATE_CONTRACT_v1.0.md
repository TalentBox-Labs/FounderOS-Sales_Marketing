# OPERATOR DEGRADED-STATE CONTRACT v1.0

**STATUS: FROZEN**  
**Source:** OF1 `OF1_DEGRADED_STATE_CONTRACT.md` (behavior unchanged)

| Condition | Display / HTTP |
|-----------|----------------|
| No pending QD | `No pending QualifiedDemand` |
| No contacts / deals | Empty degraded copy |
| No Contact↔Deal / QD↔Contact proof | `no_linked_record` |
| Deal not `closed_won` | Not in handoff list; handoff API 422 |
| closed_won, no CO | `not_yet_created` |
| CO pending decision | `pending_human_decision` |
| Operator env invalid | Actions blocked; mutations 503 |
| Duplicate / invalid transition | 422 from frozen service |
| Unauthorized / API key set | 401 |
| Snapshot source error | Attention `unavailable` — no fake zeroes |

UI must not invent success or fabricate relationships.
