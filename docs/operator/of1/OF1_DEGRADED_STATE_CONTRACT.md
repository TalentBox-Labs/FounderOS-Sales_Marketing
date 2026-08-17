# OF1 — Degraded State Contract

**Sprint:** FOUNDER OS OF1  
**Date:** 2026-08-13

| Condition | Display |
|-----------|---------|
| No pending QD | No pending QualifiedDemand |
| Contact has no Deal | `no_linked_record` |
| Deal has no contact_id | `no_linked_record` |
| Deal not closed_won | Not listed for handoff |
| closed_won, no CO | `not_yet_created` |
| CO registered, not decided | `pending_human_decision` |
| Operator env invalid | Actions blocked — set FOUNDER_OS_OPERATOR_NAME |
| DB/source error | Attention `unavailable` — no fake zeroes |
