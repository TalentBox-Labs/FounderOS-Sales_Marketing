# UI-D1 Demo Data

## Seed script

`scripts/seed_founder_demo.py` — development only, not invoked at startup.

```bash
SECRET_KEY=... DATABASE_URL=sqlite:///./founder_demo.db python scripts/seed_founder_demo.py
```

Creates:

- Demo user (`founder@demo.local` / `FounderDemo123!`)
- Organization "Demo Workspace"
- Sample contact (`/contacts/22222222-2222-2222-2222-222222222222`)
- Pending qualified demand handoff

## Full journey

Requires additional steps via UI: accept demand on `/operator`, run rev-orch actions on contact workspace, simulate reply via n8n webhook (existing M3 path).
