# UI-D2 Google Calendar Demo Scope

**Certified provider:** Google Calendar (`google_calendar` connector)

**NOT_IMPLEMENTED:** Outlook availability UI (fail-closed message when Outlook is sole connector)

Live demo may use tenant-configured Google credentials through normal M4 runtime. No demo-mode bypass. Automated tests mock `get_tenant_availability` and `create_tenant_calendar_event` only.
