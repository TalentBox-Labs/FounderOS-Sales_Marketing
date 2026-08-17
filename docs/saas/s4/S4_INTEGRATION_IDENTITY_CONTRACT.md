# S4 — Integration Identity Contract

| Identity | S4 behavior |
|----------|-------------|
| HUMAN | Session + org cookie for connector CRUD |
| SERVICE (n8n) | Secret binding → service TenantContext; not human |
| AGENT/AI | Unchanged frozen boundaries |

Webhook cannot spoof `requested_by` or human identity.
