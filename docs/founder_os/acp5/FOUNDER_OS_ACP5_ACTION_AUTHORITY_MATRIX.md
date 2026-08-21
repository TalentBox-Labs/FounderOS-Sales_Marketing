# Founder OS ACP-5 — Action Authority Matrix

**Baseline:** `founder-os-acp4-v1.0` @ `954af7b34590a45991dd098afb21235dfef71fd2`
**Rule:** Planning / UI / attention ≠ authority.

| Action | Existing work/effect | ACP-5 v1 role | Execution mode | Command surface | Authority expansion? |
|--------|----------------------|---------------|----------------|-----------------|----------------------|
| Scan follow-up eligibility | `follow_up_eligibility` | Discover | READ | Info via orchestration | NO |
| Propose follow-up | `WORK_FOLLOW_UP_PROPOSE` | Primary play | AUTONOMOUS | agent proposed / awaiting_human | NO |
| Approve/reject follow-up send | `WORK_APPROVAL_DECIDE` / `decide` | Primary play | HUMAN_REQUIRED + INLINE_GOVERNED | INLINE | NO |
| Send follow-up email | `send_outreach_email` executor | Primary play | EXECUTE_GOVERNED | Result only | NO |
| Propose booking | `WORK_BOOKING_PROPOSE` / `_run_booking_proposal` | Secondary (optional) | AUTONOMOUS propose | awaiting_human approval | NO |
| Execute booking | `book_meeting` executor | Secondary | HUMAN_REQUIRED | INLINE approve | NO |
| Research-to-outreach | existing API | **DEFER** | — | — | N/A |
| Hermes score | `WORK_LEAD_SCORE` / Hermes | Keep existing | AUTONOMOUS | orchestration | NO |
| Hermes qualify recommend | recommend-only | Optional handoff later | READ/recommend | Info / NAVIGATE | NO |
| Hermes deal create | `WORK_HERMES_DEAL_CREATE` | Sanitize plans | PROHIBITED | Never executable | NO |
| Contact status mutate | PROHIBITED autonomous | Out of scope | PROHIBITED | — | NO |
| Deal stage mutate | PROHIBITED autonomous | Out of scope | PROHIBITED | — | NO |
| QD accept/reject | COS-5 | Preserve | INLINE_GOVERNED | INLINE | NO |
| Pause/kill/resume visibility | ACP-4 gates | Oversight | Process/env | Command gates panel | NO |

## Hermes plan sanitization decision

**Decision: A + C**

- **Suppress** `create_deals_for_qualified` from `generate_plan` runnable steps for `pipeline_value` / `deals_closed`
- **Replace** with permitted observational/recommend handoffs (e.g. continue qualify recommend + at-risk flag; founder deal creation remains approval/CRM HUMAN path)

Never make PROHIBITED work executable. Prefer preventing founder/operator noise over surfacing blocked plan theater.
