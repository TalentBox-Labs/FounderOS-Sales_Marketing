# Founder OS COS-1 Vertical Slice v1

**STATUS:** DESIGN ONLY — do not implement in COS-ARCH-v1  
**Sprint:** COS-ARCH-v1  
**Baseline:** `a7463e5`

## Challenge to the prompt’s candidate

The prompt starts at Founder Context → Market / ICP → Audience. **Repository evidence disagrees.**

ICP/Audience/Campaign **entities are missing**. The **live** governed spine is:

```
QualifiedDemand → Contact → Research → Draft/Approval → Outreach
  → Follow-up → Reply → Meeting interest → Booking proposal → Approval
  → Calendar execution → Operator outcome / Deal
```

COS-1 is this spine as **one Founder journey**, plus a **minimal** company-context stub (org + user), not a greenfield Marketing graph.

Marketing engines (content/SEO) stay attached later (COS-2).

---

## Step map

| Step | Existing capability | Backend owner | Existing UI | Missing backend | Missing UI | Authority | Tenant | Event (overlay) | Read model | Tests |
|------|---------------------|---------------|-------------|---------------|------------|-----------|--------|-----------------|------------|-------|
| Founder context | User + Organization | Shared | chrome org name | attested ICP/goals | settings | human edit later | org | n/a | shell context | S1/S2 |
| Market / ICP | Marketing engines PARTIAL | Marketing | `/marketing` thin | attested strategy SoT | Company settings | human attest | org | n/a | none | engine tests, not COS |
| Audience / Lead | Lead = Contact | Revenue + QD | `/demand` | Audience entity **out of COS-1** | — | QD accept human | org | QD | demand snapshot | MC04 / UI-D1 |
| Research | M1 worker_research | Rev-orch | contact actions | — | copy polish | AI allowed | org | CONTACT_RESEARCHED | contact snapshot | M1.5 |
| Score | lead_score field | dual scorers **debt** | contact | unify scorer | — | no auto status | org | CONTACT_SCORED | contact | A4.5 / scheduler |
| Qualification | Sales policy + M1 qualification log | Sales/Rev-orch | operator + contact | — | — | human for promotion | org | QD accept | operator RM | OF1 / MC04 |
| Founder recommendation | advisory next action | Founder RM | contact / command | company context unused | Home language | advisory only | org | derived | command + contact | UI-D1.5 |
| Approval | ApprovalRequest | Shared | `/pending-approvals` | — | Home count | HUMAN | org | approval_* | approvals snapshot | UI-D2 / S3 |
| Outreach | send after approve | M1 | contact | — | — | HUMAN_APPROVAL | org | OUTREACH_* | contact | M1.5 |
| Follow-up | M2 | Rev-orch | contact | — | — | HUMAN_APPROVAL + revalidate | org | FOLLOWUP_* | contact | M2.5 |
| Reply | M3 + n8n | Rev-orch | contact reply card | — | — | classify AI; no CRM qualify | inbound tenant | REPLY_* | contact | M3.5 |
| Meeting | M4 + UI-D2 | Rev-orch + Founder UI | booking panel | — | terminology | propose AI; book after human; stale slot | org + connector | BOOKING_* / MEETING_BOOKED | attach_safe_booking | UI-D2 30 / M4.5 |
| Opportunity | Deal | Revenue | operator thin | Deal workspace **out of COS-1** | list on contact | human stage | weak tenant on Deal row | OPPORTUNITY_* | contact deals | A3.5 |
| Revenue signal | CommercialOutcome | Sales→Revenue | operator | finance SoT later | don’t fake ARR | HUMAN_ONLY | org | REVENUE_RECORDED | operator | MC06 |
| Insight / next | Command snapshot | Founder | `/command` | fold cockpit | Home rename | read | org | derived | command | UI-D1 |

---

## COS-1 in / out

**In**

- Name the spine in product language (Home, People, Person workspace, Approvals, Activity)
- Keep frozen authority/tenant/booking contracts
- Document event overlay on existing logs
- Company context **stub** (display org/user only) unless a follow-on ADR

**Out**

- New Lead/Opportunity/Audience tables
- Design-system rewrite
- SPA migration
- Forecast product
- Widening AI autonomy
- Rebuilding M1–M4

---

## Freeze gate (when COS-1 is later implemented)

- UI-D2 30/30
- M1.5–M4.5 baselines
- MC04.5 / MC06.5
- SaaS tenant isolation suites
- UI-D1.5 frozen files **untouched**; superseded absence tests remain historical
- No Contact/Deal mutation from booking UI (`test_ui_d2_contact_deal_unchanged`)
