# M0.5 Future Worker Map

**Sprint:** REV-ORCH M0.5  
**Date:** 2026-08-17  
**Status:** Planning only — not authorized for implementation in M1

---

## Rule

Future workers remain **proposal-only**. They do **not** gain:

- qualification acceptance
- pipeline stage mutation
- commercial outcome acceptance
- send execution
- calendar booking
- CRM privileged mutation

unless a **future explicit frozen contract** supersedes this map.

---

| Worker | Classification | Business boundary | Why |
|--------|----------------|-------------------|-----|
| **Follow-Up Worker** | **LIKELY** | Draft follow-up copy + proposed timing. Orchestrator/scheduler owns Activity schedule. Human approval before send. | `build_followup_sequence` and `followups.py` exist. Current sequence persist is unsafe as worker write — must become proposal. |
| **Objection Handling Worker** | **LIKELY** | Classify inbound reply + draft response. ApprovalRequest for send. | `handle_latest_reply` already proposal+approval. Needs tenant scope. |
| **Qualification Recommendation Worker** | **POSSIBLE** | Recommend Contact.status / QD accept. **Human still accepts.** | A4/MC04.5 HUMAN_ONLY. Worker may suggest; never apply. |
| **Meeting Preparation Worker** | **POSSIBLE** | Brief from Contact/Deal for a booked meeting. No calendar write. | BOOK is human + n8n inbound. Prep is read/summarize only. |
| **Pipeline Recommendation Worker** | **POSSIBLE** | Recommend Deal.stage. **Human still advances.** | A3 HUMAN_ONLY. |
| **Lead Finder Worker** | **NOT_RECOMMENDED** | FIND is existing deterministic prospecting/manual demand. | Duplicate SoT risk. |
| **Appointment Setter Worker** | **NOT_RECOMMENDED** | Would imply autonomous booking. | No native calendar; auto-book prohibited. |
| **Sales Manager Worker (autonomous close)** | **NOT_RECOMMENDED** | Would mutate pipeline/CO. | Frozen A3/MC06. |
| **LinkedIn Opener Worker** | **LIKELY** (channel expansion, not M1) | Draft only; LinkedIn send is manual (`send_linkedin_message` executor). | Already in sales_agents. |

---

## Authorization remainder

| Action | Future worker | Who executes |
|--------|---------------|--------------|
| Qualify demand | Recommend only | Human + `qualified_demand_service` |
| Advance Deal.stage | Recommend only | Human + A3 service |
| Send email | Draft only | Human ApprovalRequest + n8n |
| Book meeting | None | Human / inbound n8n signal |
| Accept CommercialOutcome | Recommend only | Human + MC06.5 |

---

*End of M0.5 Future Worker Map*
