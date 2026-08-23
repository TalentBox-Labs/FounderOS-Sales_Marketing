# Integration Identity Authority Contract v1.0

## Frozen principal kinds

| Kind | Integration S4.5 behavior |
|------|---------------------------|
| HUMAN | Session + org for connector CRUD |
| SERVICE | n8n binding → integration TenantContext; **not human** |
| AGENT | Unchanged frozen boundaries |
| AI | Unchanged frozen boundaries |

## Prohibited

- Webhook setting `requested_by` for human gates
- Connector execution acquiring HUMAN_ONLY authority
- Payload spoofing human identity

## Preserved

- `is_human_approver` on A3/A4 routes unchanged
- `requested_by` server binding on cockpit/operator/CRM human mutations
