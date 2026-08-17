# SaaS S2 — Secret Isolation Future Boundary

## Current state (S2)

Connector credentials remain **global** (`credentials_vault`). S2 does not fake tenant secret isolation.

## Future seam

```
Organization → Integration Connection → Tenant Secret
```

## Immediate risk

Global credentials could enable cross-tenant execution if wired to tenant mutations without scoping. S2 bounded slice does not activate tenant-specific integration execution.

## S2 action

Document boundary only. No tenant vault migration in S2.
