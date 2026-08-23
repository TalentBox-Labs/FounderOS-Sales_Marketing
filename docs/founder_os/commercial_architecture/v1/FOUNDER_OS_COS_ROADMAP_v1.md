# Founder OS COS Roadmap v1

**STATUS:** RECOMMENDATION  
**Sprint:** COS-ARCH-v1  
**Baseline:** `a7463e5`

## Sequence challenge

Prompt sequence: COS-1 foundation → COS-2 Marketing→Sales → COS-3 Sales execution → COS-4 Revenue intelligence → COS-5 Founder Command → COS-5.5 freeze.

**Repository-better sequence:** Sales execution (M1–M4) and Marketing→Sales intake (MC04) **already exist**. COS-2 must not rebuild QD. COS-3 must not rebuild booking. Put **Founder language + spine certification** first; attach Marketing engines second; Deal/Account workspaces third; forecast fourth; Home absorption of Operator/Cockpit fifth.

```
COS-ARCH-v1 (this pack)
 → COS-1  Commercial spine (existing journey + IA + context stub)
 → COS-2  Marketing engines → QualifiedDemand (no new CRM)
 → COS-3  Sales object workspaces (Company/Deal projections)
 → COS-4  Revenue intelligence (forecast/attribution without second CRM)
 → COS-5  Founder Command (single Home; retire duplicate cockpit)
 → COS-5.5 Integrated Founder OS freeze
```

---

## COS-ARCH-v1

| | |
|--|--|
| Objective | Repository-grounded commercial OS architecture |
| User outcome | none (docs) |
| Backend / UI | none |
| Governance | this pack |
| Gate | docs complete; no code |
| Deps | demo-runtime-v1.0 |

## COS-1 Commercial spine

| | |
|--|--|
| Objective | One Founder journey on live M1–M4 + QD + approvals |
| User outcome | Understand → decide → execute → govern on a person |
| Backend | Event overlay docs→optional log fields; no new SoT tables required |
| UI | Terminology/hierarchy in Jinja **without** weakening authority |
| Governance | Preserve all frozen matrices |
| Gate | UI-D2 30/30; M1.5–M4.5; MC04.5; tenant suites; frozen D1 files untouched |
| Deps | COS-ARCH-v1 |

## COS-2 Marketing → Sales

| | |
|--|--|
| Objective | Content/campaign/intent **produce** QD without writing Contact except via intake |
| User outcome | Founder sees demand from marketing without a second lead DB |
| Backend | QD producer completeness; attribution fields |
| UI | Marketing remains engines; People shows accepted contacts |
| Governance | Marketing v2.2 engines frozen behavior |
| Gate | MC04.5 + marketing engine baselines |
| Deps | COS-1 |

## COS-3 Sales object workspaces

| | |
|--|--|
| Objective | Account + Opportunity **projections** of Company/Deal |
| User outcome | Pipeline without alias tables |
| Backend | org_id on Deal (schema ADR); facades only |
| UI | workspaces; `/sales` as index |
| Governance | A3.5 deal stage; A4.5 scoring; no LeadScorer status bypass |
| Gate | Sales baselines + tenant CRM suites |
| Deps | COS-1; not blocked on COS-2 |

## COS-4 Revenue intelligence

| | |
|--|--|
| Objective | Funnel/forecast/attribution as **derived** read models |
| User outcome | What resulted — not a second pipeline |
| Backend | one analytics SoT plan; CO → recording |
| UI | Revenue secondary nav |
| Governance | Revenue does not duplicate CRM |
| Gate | MC06.5 + no fake ARR in templates |
| Deps | COS-3 recommended |

## COS-5 Founder Command

| | |
|--|--|
| Objective | Single Home; Operator/Cockpit absorbed or demoted |
| User outcome | What matters now / what needs me |
| Backend | merge command + cockpit read models |
| UI | rename Command Center → Home |
| Governance | still no client authority |
| Gate | UI-D1.5 nav contract unfreeze **or** additive screens only |
| Deps | COS-1 |

## COS-5.5 Integrated freeze

| | |
|--|--|
| Objective | Freeze commercial OS IA + graph + events overlay |
| User outcome | durable product language |
| Gate | full regression envelope + superseded historical tests documented |
| Deps | COS-2..5 as actually shipped |

---

## Explicitly not on the critical path

- SPA migration  
- `sales_os/` package extract (may follow C1, not COS-1)  
- Video/Newsletter/Community engines (v2.2 FUTURE)  
- Widening AI send/book autonomy  
