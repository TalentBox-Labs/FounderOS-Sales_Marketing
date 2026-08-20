# Founder OS COS-2 Marketing → Qualified Demand Contract

**Sprint:** COS-2
**Runtime truth, not aspirational architecture.**

## Path

```
Marketing signal fields (supplied)
  → compose_marketing_qualified_demand()
  → register_marketing_handoff()  # AgentActionLog qualified_demand_handoff
  → Founder People / Home presentation (read model)
  → Human accept/reject on existing Operator intake
  → Contact SoT only on accept (MC04)
```

## Presentation fields (pending demand)

| Founder language | Source | If missing |
|------------------|--------|------------|
| Identity | payload.person name/email | demand_id |
| Demand source | payload.source mapped to label | “Source not stored” |
| Why it matters | marketing_qualification.reason/notes/summary or tier+score | Honest: no extra notes stored |
| Signals | channel + content_attribution keys actually present | Omit or “No extra stored signals” |
| Needs your decision | pending (not accepted/rejected) | n/a |
| What happens next | Fixed copy: accept adds to People; marketing cannot send/book/change deals | n/a |
| Workspace context | Organization.name | omitted |
| Company hint | payload.company_hint.name (payload only; **no Company table lookup**) | omitted |

## Authority classes

| State | Class | Meaning |
|-------|-------|---------|
| Handoff registered | SYSTEM_RECOMMENDED | Marketing/founder proxy asserted qualification; not a human intake decision |
| Accept / reject | HUMAN_DECIDED | Existing operator intake |
| Contact created | SYSTEM_EXECUTED after human accept | MC04 |

## Not in this contract

- New `qualified_demands` table
- Automatic Contact insert on handoff
- Contact.status / Deal.stage writes from marketing
- Fabricated ICP, ARR, CAC, campaign SoT
- Duplicate research/outreach/booking UI
