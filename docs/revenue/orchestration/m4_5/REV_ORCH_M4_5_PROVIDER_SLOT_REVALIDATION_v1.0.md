# REV-ORCH M4.5 — Provider Slot Revalidation v1.0

## M4 defect (found during freeze)

M4 execution revalidated only that the selected slot was **in the future**.
`create_tenant_calendar_event` could create against a slot that became busy
between T1 availability query and T3 approved execution.

## Containment (M4.5)

`calendar_executor.revalidate_provider_slot()` runs immediately before
`GoogleCalendarClient.create_event` / Outlook create.

Google: `GoogleCalendarClient.has_busy_overlap(calendar_id, start, end)`
- True → booking blocked ("Selected slot is no longer available")
- Provider error → fail closed
- Unconfigured → fail closed

Outlook: fail closed (availability cannot be confirmed)

Past / naive timestamps: normalized to UTC; past slots blocked.

## Contract
```
PROVIDER_LEVEL_SLOT_REVALIDATION = PASS
STALE_SLOT_RACE = BLOCKED
```
