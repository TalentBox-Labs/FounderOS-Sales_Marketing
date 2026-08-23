# UI-D2 Tenant Security Attestation

Verified in `tests/test_ui_d2_live_governed_booking.py`:

1. Cross-tenant availability → 422
2. Cross-tenant propose → 422
3. Cross-tenant approval inbox isolation
4. Cross-tenant approve blocked
5. Client `organization_id` spoof ignored on propose
6. Client `decided_by` spoof does not establish human identity
7. No credential/secret exposure in HTML
8. Outlook availability fail-closed in UI
