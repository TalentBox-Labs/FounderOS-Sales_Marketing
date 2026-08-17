# REV-ORCH M2.5 — Cadence Contract v1.0

**STATUS: FROZEN**  
**FOLLOWUP_CADENCE_v1 = FROZEN**

## Policy constants

```
MAX_FOLLOW_UP_STEPS = 2
FOLLOW_UP_INTERVALS_DAYS = (3, 7)
```

Defined in `revenue_os/services/follow_up_eligibility.py`.

## Semantics

- Step 1 due 3 days after last completed outbound email.
- Step 2 due 7 days after last completed outbound email.
- After 2 completed follow-ups: `FOLLOWUP_CADENCE_COMPLETE`.
- Interval not elapsed: `FOLLOWUP_NOT_DUE`.
- Cadence is deterministic, inspectable, reply-aware, stop-aware.
- FollowUpWorker may recommend `recommended_send_after` only after eligibility passes; it cannot change step count or interval policy.

Future cadence changes require an explicit baseline version bump. Do not silently edit these constants.
