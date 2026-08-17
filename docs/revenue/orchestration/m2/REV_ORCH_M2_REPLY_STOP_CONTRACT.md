# REV-ORCH M2 — Reply Stop Contract

## Reply signals (repository reality)

| Source | Signal |
|--------|--------|
| `Activity` | `direction=inbound`, types `EMAIL`, `EMAIL_REPLY`, `LINKEDIN_MESSAGE` |
| n8n webhook `email.replied` | Creates `Activity` type `EMAIL_REPLY` (inbound) when contact resolved |

## Stop rules

1. **Before proposal** — eligibility returns `FOLLOWUP_REPLY_RECEIVED`; no FollowUpWorker run
2. **After approval, before send** — `_revalidate_follow_up_before_send` blocks n8n handoff
3. **After send** — next eligibility evaluation detects inbound reply → cadence stops

## Not in M2 scope

Automatic Contact.status or Deal.stage promotion on reply — unchanged from M1.5.

## Tests

- `test_m2_reply_before_proposal_blocks`
- `test_m2_reply_after_approval_blocks_send`
