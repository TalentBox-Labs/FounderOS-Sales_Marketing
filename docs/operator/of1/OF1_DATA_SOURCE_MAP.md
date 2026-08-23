# OF1 — Data Source Map

**Sprint:** FOUNDER OS OF1  
**Date:** 2026-08-13

Presentation composition only. No persisted view model.

| UI block | Authoritative source |
|----------|----------------------|
| Pending demand | `AgentActionLog` `qualified_demand_handoff` minus accept/reject |
| Contacts | `Contact` + stored `lead_score` + `LeadScorer.suggest_status_from_score` |
| QD↔Contact | Accept audit `contact_id` |
| Contact↔Deal | `Deal.contact_id` |
| Deals | `Deal` + A3.5 stage sets |
| Pending CO handoff | `Deal.stage=closed_won` minus open/accepted outcome |
| Pending Revenue | `commercial_outcome_handoff` minus accept/reject |
