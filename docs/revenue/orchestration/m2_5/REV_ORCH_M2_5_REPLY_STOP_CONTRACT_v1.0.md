# REV-ORCH M2.5 — Reply Stop Contract v1.0

**STATUS: FROZEN**  
**REPLY_STOP_CONTRACT = FROZEN**

## Reply signals (repository reality)

| Source | Signal |
|--------|--------|
| Activity | `direction=inbound` and type in `{EMAIL, EMAIL_REPLY, LINKEDIN_MESSAGE}` |
| n8n `email.replied` | Creates inbound `ActivityType.EMAIL_REPLY` when contact is tenant-resolved |

## Frozen rules

| Moment | Behavior |
|--------|----------|
| Reply before proposal | Eligibility `FOLLOWUP_REPLY_RECEIVED`; no FollowUpWorker; HTTP 422 |
| Reply while pending | Approve path revalidates; n8n not called; `executed=false` |
| Reply after approval before send | Same revalidation (approve executes synchronously after decision) |
| Reply after send | Next eligibility is `FOLLOWUP_REPLY_RECEIVED` |
| Scheduler tick | `evaluate_follow_up_eligibility` sees inbound Activity; does not propose |

AI, scheduler, and n8n cannot override a recorded valid reply.
