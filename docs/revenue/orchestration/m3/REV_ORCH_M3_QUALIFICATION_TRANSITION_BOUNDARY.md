# REV-ORCH M3 — Qualification Transition Boundary

| Reply | Recommendation | Mutation |
|-------|----------------|----------|
| INTERESTED | QUALIFY, suggested_contact_status=qualified | none |
| MEETING_INTEREST | QUALIFY + BOOKING_ELIGIBLE | none |
| NOT_INTERESTED | DISQUALIFY, suggested churned | none |
| OPT_OUT | SUPPRESS | Contact.tags += unsubscribed (M2.5 stop tokens) |
| UNKNOWN / AI fail | HUMAN_REVIEW | none (Activity kept) |

Contact.status remains A4 human `apply_contact_status_update`.  
Deal.stage remains A3 human.  
QualifiedDemand accept remains MC04.5 human `accept_qualified_demand`.
