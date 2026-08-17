# MANUAL DEMAND IDEMPOTENCY CONTRACT v1.0

**STATUS: FROZEN**  
**Authoritative owner:** MC04.5 `register_marketing_handoff`

| Case | Behavior |
|------|----------|
| Same `demand_id` registered twice | `{idempotent: true}`; one `qualified_demand_handoff` audit row |
| New `demand_id`, same email | New handoff allowed; Contact merge only on later Sales accept |
| Register without accept | No Contact row |
| Accept after register | Canonical Contact create/merge (MC04.5) |
| Replay after success | Idempotent if same demand_id |

No unintended duplicate Contact/Deal/Revenue state from registration alone.
