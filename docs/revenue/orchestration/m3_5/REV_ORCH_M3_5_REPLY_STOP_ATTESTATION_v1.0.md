# REV-ORCH M3.5 — Reply Stop Attestation v1.0

## Status: FROZEN

## M2.5 Reply-Stop Preservation

M3 inbound reply handling creates `Activity(activity_type=EMAIL_REPLY, direction=inbound)`.

`evaluate_follow_up_eligibility()` in follow_up_eligibility.py checks:
- `_has_inbound_reply_after(db, contact_id, source_at)` — any inbound reply after initial
  outreach stops follow-up eligibility → `FOLLOWUP_REPLY_RECEIVED`

This contract is UNCHANGED by M3.

## OPT_OUT Stop

OPT_OUT classification adds "unsubscribed" to Contact.tags.
`_contact_stop_tags()` checks for "unsubscribed" in `_STOP_TAGS` → `FOLLOWUP_STOPPED`.

## Stale Authority Revalidation

At follow-up execution time, eligibility is re-evaluated. If a reply arrived between
proposal and execution, the follow-up is blocked.

## Contract

```
M2_5_REPLY_STOP = PRESERVED
STALE_FOLLOWUP_AFTER_REPLY = BLOCKED
OPT_OUT_FOLLOWUP = BLOCKED
STALE_AUTHORITY_REVALIDATION = PASS
```
