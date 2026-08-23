# OF1 — Operator Flow Contract

**Sprint:** FOUNDER OS OF1  
**Date:** 2026-08-13

| Stage | Read | Mutation |
|-------|------|----------|
| Demand intake | Pending MC04 handoffs | Accept / reject (MC04.5) |
| Qualification | Contact + stored score + LeadScorer recommendation (non-mutating) | Contact.status (A4.5) |
| Deal progression | Deal + A3.5 permitted stages | Stage update (A3.5); create discovery–negotiation only |
| Closed-won / CO | closed_won without open/accepted outcome | MC06.5 handoff |
| Revenue decision | Open CO handoff | MC06.5 accept / reject |

Marketing QualifiedDemand **register** is not exposed (Audience→Demand deferred).

Relationships: QD→Contact only after accept audit; Contact→Deal only via `Deal.contact_id`. Otherwise `no_linked_record` / `not_yet_created`.
