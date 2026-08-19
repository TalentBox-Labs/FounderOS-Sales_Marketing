# Founder OS Domain Ownership Matrix v1

**STATUS:** ARCHITECTURE ONLY  
**Sprint:** COS-ARCH-v1  
**Baseline:** `a7463e5`

Binding predecessors: ADR-004/005, Sales OS architecture baseline, Marketing OS v2.2, Revenue M0.5–M4.5, UI-D1.5/D2.

---

## 1. Domain missions (customer language)

| Domain | Mission |
|--------|---------|
| **Marketing OS** | Discover market, express positioning, run content/channels, create **intent**, qualify **marketing** demand |
| **Sales OS** | Research, score (policy), qualify **sales**, engage, follow up, handle replies, propose meetings, move **deals** |
| **Revenue OS** | Own CRM **records**, values, close recording, forecast, revenue intelligence |
| **Founder OS** | Synthesize attention, recommendations, approvals, company context, goals, authority supervision |

Platforms: AI (no commercial SoT), Automation (transport), Shared (identity, tenant, secrets, audit infra).

---

## 2. Ownership matrix

| Concern | Marketing | Sales | Revenue | Founder | Platform |
|---------|-----------|-------|---------|---------|----------|
| Campaign content / editorial / publish / SEO | **SoT** | no | no | supervise | Automation executes jobs |
| Marketing qualification | **SoT** | consume via QD | no CRM write from marketing | accept/reject visibility | — |
| QualifiedDemand event | produce | **intake SoT** | Contact persist is Revenue | Operator UI | log infra |
| Contact / Company / Deal / Pipeline / Activity | no | ops via facade | **SoT** | read models | tenant filters |
| Outreach sequence **ops** | no | **ops** | persist Activity | approve send | — |
| `OutreachSequence` table | no | ops | schema host | — | — |
| Follow-up / reply / booking workflows | no | policy + workers | eligibility reads CRM | UI + approvals | orchestrator |
| Calendar credentials | no | no | no | settings | **Shared / S4** |
| Forecast / ARR recognition | no | emit CommercialOutcome | **SoT** (future finance) | view | — |
| Company context / ICP / founder prefs | contribute copy | consume | no | **SoT (proposed)** | User.preferences stub |
| Approvals queue | editorial approvals exist separately | sales actions | revenue-impacting | **founder inbox** | `ApprovalRequest` |
| Human vs AI | editorial human | proposal-only | no AI close | **authority UX** | `require_human_mutation_authority` |

---

## 3. Overlaps — single SoT + primary owner

| Overlap | SoT | Primary owner | Secondary |
|---------|-----|---------------|-----------|
| Person | `Contact` | Revenue | Sales ops, Marketing must not insert except via QD |
| Account | `Company` | Revenue | Sales language “Account” |
| Opportunity | `Deal` | Revenue | Sales stage ops |
| Intent before CRM | QualifiedDemand log | Sales intake after produce | Marketing produce |
| Timeline | `Activity` | Revenue | Sales writes via services |
| Audit | `AgentActionLog` | Shared | all producers |
| Meeting booked | Deal/Contact unchanged; calendar + Activity | Revenue Activity + M4 executor | Sales/Founder propose |
| Pipeline (sales process vs forecast) | `Deal.stage` + `Pipeline` | Revenue field | Sales process owner |
| Content | FS tracker (frozen Marketing) | Marketing | Founder does not edit SoT in Command |
| Scoring | Contact.lead_score field | Revenue field | Sales policy; **dual scorer services = debt** |
| Goals | Hermes `Goal` vs company goals | Split: planner vs Founder context | do not merge |

---

## 4. Marketing OS boundary

**Owns:** Content Studio, Editorial, Publishing, Website, Campaign, SEO/GEO/AEO, Social, Email, Brand engines (v2.2); marketing qualification; QD **payload production**.

**Does not own:** Contact/Deal tables; sales send; booking; forecast; tenant identity.

**LIVE UI:** `/marketing`, `/content-studio`, `/editorial`, `/publishing`, `/seo`, `/weeks`.

---

## 5. Sales OS boundary

**Owns:** Prospecting plans, outreach **operations**, sales qualification **workflow**, pipeline **ops**, sales agents (draft only), QD **accept/reject**, CommercialOutcome **emit**.

**Does not own:** CRM schema; billing; publish; LLM infra.

**LIVE UI:** `/sales`, contact workspace actions, `/operator` sales steps.

**Physical code:** still under `revenue_os/` (ACCEPTED_LEGACY).

---

## 6. Revenue OS boundary

**Owns:** `Company`, `Contact`, `Deal`, `Pipeline`, `Activity`; deal value/probability/dates; forecast **destination**; CRM APIs (current runner CRM = ACCEPTED_LEGACY facade).

**Does not own:** becoming a second sales engagement product; silent qualification from reply (M3.5: meeting interest ≠ qualified write).

**LIVE:** models + orchestration M1–M4 + booking executor + commercial_outcome_service.

---

## 7. Founder OS boundary

**Owns:** Cross-domain read models (`founder_ui_read_model`, `cockpit_read_model`, `operator_flow_read_model`); approval UX; attention; proposed company context; terminology.

**Does not own:** New lifecycles in Jinja; client-side authority; duplicate CRM.

**LIVE UI:** `/command`, `/demand`, `/contacts/{id}`, `/pending-approvals`, `/activity`, `/cockpit` (legacy), `/login`.

---

## 8. Handoff contracts (unchanged law)

```
Marketing  --QualifiedDemand-->  Sales intake  --Contact SoT-->  Revenue
Sales      --CommercialOutcome--> Revenue intake
```

Implementation: QD LIVE; CommercialOutcome service LIVE (human-triggered); A1.5 docs still say NOT_IMPLEMENTED for CO in places — **conflict: code wins for existence, freeze still governs payload/authority**.
