# Founder OS Commercial Event Contract v1

**STATUS:** ARCHITECTURE ONLY  
**Sprint:** COS-ARCH-v1  
**Baseline:** `a7463e5`

Events in this repository are **not** a dedicated event bus. Persistence is primarily `AgentActionLog` plus `ApprovalRequest` plus CRM row changes. Automation Platform (Celery/n8n) is transport, not SoT.

Canonical overlay names below are **documentation**. Runtime continues to use existing `action_type` strings until a dedicated event sprint.

---

## 1. Existing producers (audit)

| Runtime `action_type` / artifact | Producer | Approx overlay |
|----------------------------------|----------|----------------|
| `qualified_demand_handoff` | `qualified_demand_service` | LEAD_QUALIFIED / DEMAND_HANDED_OFF |
| `qualified_demand_accepted` / `_rejected` | same | DEMAND_ACCEPTED / REJECTED |
| `commercial_outcome_handoff` / accepted / rejected | `commercial_outcome_service` | REVENUE_RECORDED (closed_won only) |
| `rev_orch_workflow_started` | `revenue_orchestration_service` | WORKFLOW_STARTED |
| `worker_research` / `rev_orch_qualification` | M1 | CONTACT_RESEARCHED / CONTACT_SCORED (partial) |
| `send_outreach_email` (approval) | M1 / sales_agents | OUTREACH_PROPOSED |
| `worker_personalize` | M1 | derived |
| `rev_orch_followup_eligibility` / `worker_followup_proposal` | M2 | FOLLOWUP_PROPOSED |
| `rev_orch_reply_assessment` / `worker_reply_analysis` | M3 | REPLY_ASSESSED / MEETING_INTEREST_DETECTED |
| `rev_orch_booking_eligibility` / `book_meeting` / `worker_booking_proposal` | M4 | BOOKING_PROPOSED |
| `approval_requested` / `approval_approved` / `approval_rejected` | `approvals.py` | *_APPROVED / *_REJECTED |
| `lead_scored` | scheduler | CONTACT_SCORED |
| `followup_proposal_scheduled` | scheduler | FOLLOWUP_PROPOSED |
| `deal_at_risk_flagged` | scheduler | derived risk |
| `goal_created` / `goal_checked` / `goal_achieved` | Hermes | not commercial ARR |
| Editorial / publishing jobs | Marketing routers | CAMPAIGN_* not unified |
| n8n inbound reply | integrations | REPLY_RECEIVED |

CRM mutations (Contact insert, Deal.stage) are **SoT changes**, not always logged as overlay events.

---

## 2. Overlay catalog

Legend: **P** persistent SoT · **D** derived · **H** human authority impact.

Tenant: every commercial event must carry `organization_id` (nullable logs are **debt**).  
Provenance: `AgentActionLog` row or ApprovalRequest id.  
Idempotency: existing keys (`demand_id`, booking proposal hashes, approval id).  
Replay: reconstruct from logs + CRM; do not replay into calendar/CRM without revalidation.

### Demand / people

| Overlay | Existing | Producer | Consumers | P/D | Authority | Idempotency |
|---------|----------|----------|-----------|-----|-----------|-------------|
| LEAD_CREATED | Contact insert on QD accept | Sales intake / Revenue persist | Founder People, scoring | P Contact | human accept | email merge + demand_id |
| LEAD_QUALIFIED (marketing) | QD handoff | Marketing | Sales Operator | D log | marketing policy; Sales may reject | demand_id |
| CONTACT_RESEARCHED | `worker_research` | M1 | UI workspace | D log | AI research allowed | workflow execution |
| CONTACT_SCORED | `lead_scored` / qualification | scheduler / M1 | UI score | P `lead_score` | **policy**; auto-status write is gap | contact+run |

### Outreach / follow-up

| Overlay | Existing | Producer | Consumers | P/D | Authority | Idempotency |
|---------|----------|----------|-----------|-----|-----------|-------------|
| OUTREACH_PROPOSED | `send_outreach_email` pending approval | M1 / agents | Approvals | P ApprovalRequest | HUMAN_APPROVAL_REQUIRED | approval id |
| OUTREACH_APPROVED | `approval_approved` | human | executor | P | session human | approval id |
| OUTREACH_SENT | execution result / Activity EMAIL | executor | timeline | P Activity | after approval + revalidation | message/activity id |
| FOLLOWUP_PROPOSED | M2 worker + scheduler | M2 | Approvals | P | HUMAN_APPROVAL_REQUIRED | M2.5 contracts |
| FOLLOWUP_SENT | send after approval | M2 | timeline | P | same | M2 idempotency |

### Reply / meeting

| Overlay | Existing | Producer | Consumers | P/D | Authority | Idempotency |
|---------|----------|----------|-----------|-----|-----------|-------------|
| REPLY_RECEIVED | n8n inbound | Automation | M3 | D/P log | tenant resolve inbound | M3.5 |
| REPLY_ASSESSED | `rev_orch_reply_assessment` | M3 | Contact UI | D | AI classify; **no Contact.status write** | latest assessment isolation |
| MEETING_INTEREST_DETECTED | assessment flag | M3 | booking eligibility | D | not booking authority | same |
| BOOKING_PROPOSED | `book_meeting` approval | M4 / UI-D2 | Approvals | P | HUMAN_APPROVAL_REQUIRED | proposal idempotency |
| BOOKING_APPROVED | approval_approved | human | calendar executor | P | session; revalidate slot | M4.5 |
| MEETING_BOOKED | execution + optional MeetingActivity | M4.5 executor | UI confirmation | P calendar + log | after approve; stale slot fail closed | booking idempotency |

### Pipeline / revenue

| Overlay | Existing | Producer | Consumers | P/D | Authority | Idempotency |
|---------|----------|----------|-----------|-----|-----------|-------------|
| OPPORTUNITY_CREATED | Deal insert | Sales/Revenue services | Operator | P Deal | human/policy | deal id |
| OPPORTUNITY_STAGE_CHANGED | Deal.stage | Sales ops adapter | Revenue forecast | P | human accountability | deal+stage |
| DEAL_WON / DEAL_LOST | stage enum | Sales ops | CO eligibility | P | human | deal id |
| REVENUE_RECORDED | `commercial_outcome_handoff` | Sales human | Revenue intake | P log | HUMAN_ONLY; no Deal mutate in MC06 | outcome_id |

### Marketing (overlay; not unified runtime)

| Overlay | Existing | Notes |
|---------|----------|--------|
| CAMPAIGN_STARTED / ENGAGED | engine-specific | Do not invent bus until Campaign SoT ADR |
| ATTRIBUTION_UPDATED | QD attribution + analytics_depth | Derived; not CRM write |

---

## 3. Coupling rule

Domains consume **logs + read models**, not each other’s tables, except Revenue SoT via facades.

Forbidden: Marketing writing `Deal`; UI writing eligibility; workers executing calendar before approval.

---

## 4. Human / AI impact (default)

| Class | AI | Human |
|-------|----|-------|
| Research, score, classify, recommend | allowed | supervise |
| Outbound send, follow-up send, book meeting, QD accept, CO handoff, Contact/Deal mutation | propose or blocked | required |
| Credential / tenant spoof | prohibited | n/a |
