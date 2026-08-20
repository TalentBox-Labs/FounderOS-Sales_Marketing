# Founder OS COS-4 Commercial Funnel Contract

**STATUS:** IMPLEMENTED (semantic correction v1)
**Composer:** `revenue_os/services/commercial_funnel_intelligence.py`
**Surface:** `build_command_center_snapshot` → `/command`

## Founder question

> Is commercial demand turning into pipeline and outcomes, where is it stuck, and what requires my attention?

## Snapshot shape (in-memory dict — not a table)

| Section | Meaning |
|---------|---------|
| `summary` | Compact counts for Command Center stats |
| `funnel.demand` | QualifiedDemand band (unique demand_id) |
| `funnel.pipeline` | Open sales Deal band |
| `funnel.outcome` | Terminal sales deals + unique MC06 outcomes |
| `pipeline` | Open deal stage distribution + ignored counts |
| `outcomes` | MC06 pending lists + unique accepted/rejected |
| `attention.entries` | Deterministic stuck-state reasons (not scores) |
| `recent_movement` | Recent org-scoped AgentActionLog labels |
| `provenance` | Source list + organization_id + reconciliation notes |

## QualifiedDemand reconciliation

Stable key: `AgentActionLog.target_id` = `demand_id`.

| Presentation state | Rule |
|--------------------|------|
| **accepted** | unique demand_ids with `qualified_demand_accepted` |
| **rejected** | unique demand_ids with `qualified_demand_rejected` minus accepted |
| **pending** | unique handoff demand_ids minus accepted minus rejected |

Pending presentation rows are also deduped by `demand_id` (`dedupe_pending_demands`).

Raw AgentActionLog event totals (if present) live only under `funnel.demand.event_counts` and are labeled as **events**, never as unique demand outcomes.

## Commercial outcome reconciliation

Stable key: `AgentActionLog.target_id` = `outcome_id`.

| Field | Semantics |
|-------|-----------|
| `commercial_outcome_accepted` | unique outcome_ids with accept |
| `commercial_outcome_rejected` | unique outcome_ids with reject (minus accepted) |
| `event_counts.handoff_events` | raw handoff **events** (audit only) |
| `pending_outcome_handoff` / `pending_outcome_decision` | WIP/attention only (operator flow) |

Handoff events are **never** summed into realized accepted/rejected outcomes.

## Deal stage classification

| Set | Stages |
|-----|--------|
| `SALES_OPEN_STAGES` | discovery, qualified, proposal, negotiation |
| `SALES_WON_STAGES` | closed_won |
| `SALES_LOST_STAGES` | closed_lost |
| `NON_SALES_STAGES` | sourcing, screening, interview, offer, placed, rejected |

Unknown / unsupported stages → `ignored_unknown` (not open).
Non-sales stages → `ignored_non_sales` (not open commercial pipeline).

## Funnel mapping

### DEMAND band

| Count | Source |
|-------|--------|
| `pending_intake` | unique pending demand_ids |
| `accepted` / `rejected` | unique demand_ids |
| `event_counts.*` | raw event totals (labeled events) |

### PIPELINE band

| Count | Source |
|-------|--------|
| `open_deals` / `by_stage` | Deal rows in `SALES_OPEN_STAGES` only |
| `people` | Contact count — **context only**, not pipeline total |
| `ignored_non_sales` / `ignored_unknown` | excluded from open |

### OUTCOME band

| Count | Source |
|-------|--------|
| `deals_closed_won` / `deals_closed_lost` | Deal stage in won/lost sets |
| `commercial_outcome_accepted` / `rejected` | unique outcome_ids |
| `pending_outcome_*` | WIP only |
| `event_counts.*` | raw MC06 events (labeled events) |

## Attention reason codes

| Code | Trigger |
|------|---------|
| `pending_qualified_demand` | Unique pending QD |
| `pending_approval` | Pending ApprovalRequest |
| `pending_commercial_outcome_handoff` | closed_won without MC06 handoff |
| `pending_commercial_outcome_decision` | MC06 handoff without accept/reject |
| `follow_up_eligible` | Follow-up eligibility (when provided) |
| `meeting_interest_ready` | Booking-eligible meeting interest (when provided) |

No numeric priority. No AI scores.

## Fail closed

`compose_commercial_funnel_snapshot(organization_id=None)` → `state=unavailable`, empty funnel.

## Explicitly omitted metrics

- ARR, MRR, cash collected
- Finance-grade expected revenue
- Weighted forecast / probability aggregates
- Unsupported attribution
- Company-level concentration
- Conversion percentages

## COS-3 relationship

COS-4 **composes alongside** COS-3. `decision_items_total` references COS-3 item count only; decision semantics remain in `commercial_decision_loop.py`.
