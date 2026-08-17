# REV-ORCH M2.5 — Stop / Unsubscribe Contract v1.0

**STATUS: FROZEN**  
**FOLLOWUP_STOP_CONTRACT = FROZEN**

## Supported Contact.tags tokens (M2)

`do-not-contact`, `dnc`, `unsubscribed`, `stop`

Tokenization: lowercase; split on comma/whitespace.

## Behavior

- Eligibility returns `FOLLOWUP_STOPPED` — no proposal.
- Send-time `_revalidate_follow_up_before_send` raises if tags appeared after proposal — n8n not called.
- Human approval cannot override stop tags in v1.0.
- AI cannot override.
- Scheduler cannot override.

No dedicated DNC table exists; freeze is on this tag contract only.
