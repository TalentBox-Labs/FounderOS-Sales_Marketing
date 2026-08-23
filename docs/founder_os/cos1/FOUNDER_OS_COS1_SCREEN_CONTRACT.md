# Founder OS COS-1 Screen Contract

Routes unchanged.

| Screen | Route | Founder language | Primary testids |
|--------|-------|------------------|-----------------|
| Home | `/command` | Command Center (frozen nav) | `command-approvals`, `command-demand`, `command-spine-intro` |
| People | `/demand` | People (page title); nav still Demand & Contacts | `contacts-list`, `demand-pending`, `contact-row` |
| Person | `/contacts/{id}` | Person workspace | `contact-details`, `contact-attention`, `contact-workflow`, `contact-reply`, `contact-followup`, `contact-booking-panel`, `contact-timeline`, `contact-deals`, `contact-ai-work` |
| Approvals | `/pending-approvals` | Approvals | `approvals-pending`, `approve-btn` |
| Activity | `/activity` | Activity | `activity-timeline`, `activity-event-type` (raw `action_type` retained for INT-D2) |
| Operator | `/operator` | Unchanged; not primary mental model | existing |

Empty/error: existing `*-unavailable` / `contact-not-found` retained.
