# REV-ORCH M4.5 — Timezone Contract v1.0

## Frozen behavior
- Availability slots emitted as UTC ISO8601 (`astimezone(timezone.utc).isoformat()`)
- Execution parses `Z` and `+00:00`; naive timestamps treated as UTC
- Google event create uses `"timeZone": "UTC"`
- Past-slot comparison uses `datetime.now(timezone.utc)`
- Provider overlap check requires timezone-aware start/end

## Prohibited
Silent per-tenant timezone assumptions. Contact timezone is not an authority input in M4.
