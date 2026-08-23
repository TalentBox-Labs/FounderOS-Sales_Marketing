# UI-D1.5 Demo Data Attestation v1.0

**STATUS: FROZEN**

## Mechanism

`scripts/seed_founder_demo.py`

- Invoked only as `python scripts/seed_founder_demo.py`
- `if __name__ == "__main__": seed()`
- **Not** imported by `runner_api.py` startup
- Development/demo-only; does not contaminate production initialization

## Entities created (idempotent lookups)

| Entity | Identity |
|--------|----------|
| Organization | slug `demo-workspace`, name from `FOUNDER_DEMO_ORG` |
| User | `FOUNDER_DEMO_EMAIL` (default `founder@demo.local`), hashed password |
| Membership | owner / active |
| Contact | id `22222222-2222-2222-2222-222222222222` (Alex Prospect) |
| Qualified demand handoff | id `11111111-1111-1111-1111-111111111111` via `register_marketing_handoff` |

No connector credentials, API keys, or extra tenants. Repeat runs skip existing rows.

## Not created

Deals, approvals, inbound replies, bookings. Full journey after seed uses UI + (for replies) M3 webhook/API simulation.
