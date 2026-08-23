# OPERATOR FLOW TOPOLOGY v1.0

**STATUS: FROZEN**  
**Baseline:** Founder OS Operator Flow v1.0

| Edge | Status | Proven by | Operator composition |
|------|--------|-----------|----------------------|
| QualifiedDemand → Contact | **OPERABLE** | MC04.5 accept | `POST .../qualified-demand/accept` |
| Contact → Deal | **OPERABLE** | `Deal.contact_id` + create | `POST .../deal/create` (non-terminal stages) |
| Deal → Closed-Won | **OPERABLE** | A3.5 `apply_deal_stage_update` | `POST .../deal/stage` |
| Closed-Won → CommercialOutcome | **OPERABLE** | MC06.5 handoff | `POST .../commercial-outcome/handoff` |
| CommercialOutcome → Revenue Decision | **OPERABLE** | MC06.5 accept/reject | `POST .../commercial-outcome/accept\|reject` |

Operator layer is **composition only**. It is not a SoT.

Unproven links display `no_linked_record` / `not_yet_created`. No mapping table.
