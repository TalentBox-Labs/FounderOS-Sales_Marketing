# REV-ORCH M4.5 — Availability Attestation v1.0

## Google
`GoogleCalendarClient.get_free_slots()` — OPERABLE when tenant credentials exist.
Lists events over the next 7 days and derives free intervals.

## Outlook
`get_tenant_availability()` configures Outlook then returns **empty slots**.
Outlook availability is NOT_IMPLEMENTED.

## Execution consequence
`revalidate_provider_slot()` fails closed for Outlook:
"Outlook availability cannot be confirmed at execution time — booking blocked"

Outlook event create is therefore not reachable through canonical M4 until availability exists.

## Residual
Do not claim universal calendar availability. Google path only is operable.
