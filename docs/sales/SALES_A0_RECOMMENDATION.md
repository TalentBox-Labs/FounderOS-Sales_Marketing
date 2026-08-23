# SALES A0 — Recommendation (for SALES A1)

**Sprint:** SALES A0  
**Date:** 2026-08-13  
**Next:** SALES A1 — Sales OS Architecture & Domain Boundary (**docs/ADR only — not authorized to implement here**)

---

## 1. Retain

- Jinja `/sales` prospecting operator path  
- Runner CRM APIs for contacts/deals/activities/followups (as current live CRM surface)  
- Outreach sequence models + approval queue pattern  
- Sales agent **assist** endpoints (generate, don’t send)  
- Hermes score/qualify/pipeline-health APIs (with scoring governance fix planned later)  
- SQLAlchemy Company/Contact/Deal/Activity/Pipeline models  
- React `frontend/` source as candidate CRM UI asset  
- Separation of Revenue approvals from Editorial approvals  

---

## 2. Eventually refactor (do not in A0)

- Dual API stacks (runner CRM vs JWT `revenue_os.main`) → single Sales/Revenue contract  
- Dual lead scorers → one scoring SoT + explicit human gate for status promotion  
- `DealStage` recruitment mix → split enums or domains  
- Pipeline.stages CSV vs enum  
- Co-location of Sales ops inside `revenue_os/` → package boundary after ADR  
- Alembic empty revision vs `create_all`  

---

## 3. Dead / abandoned

- `MeetingActivity` writers absent  
- In-memory marketing nurture profiles as CRM leads  
- Treating RevenueOS LinkedIn UGC publisher as Sales SoT  
- Relying on unmounted `/app` as if it were the live shell  

`frontend/` itself is **not** abandoned — **UNMOUNTED**.

---

## 4. Genuinely missing

1. Explicit Sales OS code/ownership boundary (`sales_os` or ADR-equivalent)  
2. Ratified Lead/Opportunity naming  
3. Marketing → Sales demand handoff  
4. Runner deal stage update + writable pipeline UI path  
5. Close → Customer/Client handoff  
6. Owner/RBAC enforcement  
7. Companies operator UI  
8. Relational pipeline stages  
9. Dedicated CRM test pack  

---

## 5. Proposed Sales OS domain boundary

**Sales OS owns:** prospecting, outreach sequence **ops**, SDR workflows, sales activity execution UX, qualification **workflows**, pipeline **ops** (stage movement as sales process).

**Sales OS does not own:** Shared auth/RBAC engine, Celery substrate, model providers, Marketing publish/editorial, Website/SEO.

---

## 6. Proposed Sales ↔ Revenue OS contract

| Concern | Owner |
|---------|-------|
| Contact/Company/Deal **entities** (system of record) | **Revenue OS** (per Architecture law) |
| Forecast, revenue automations, GTM revenue decisions | **Revenue OS** |
| Prospecting/outreach/SDR **workflows** consuming CRM entities | **Sales OS** |
| Approvals for outbound/revenue-impacting actions | **Revenue OS** queue; Sales files requests |
| CSM health / expansion | **Revenue OS** (or future CS OS) — not Marketing |

A1 must publish an ADR resolving migration-doc CRM-under-Sales vs Architecture CRM-under-Revenue.

---

## 7. Proposed Marketing ↔ Sales contract

| Concern | Owner |
|---------|-------|
| Content → Editorial → Publish → Website/Social | **Marketing OS** |
| Qualified demand handoff (future) | Event/API contract; Marketing emits, Sales/Revenue ingests Contact |
| Campaign sequences vs Sales outreach | Distinct; do not merge |
| No Editorial approval reuse for CRM | Already ADR-enforced |

---

## 8. Proposed human/agent authority

| Action | Authority |
|--------|-----------|
| Generate research/email/sequence drafts | Agent OK |
| Mutate Contact.status / Deal.stage | **Human** (or explicit Founder-approved policy) |
| Send email / LinkedIn message | **Human approve** |
| Create deals from autonomous planner | **Human approve** |
| Delete CRM records | **Human** |
| Enable automations that contact prospects | **Human + Revenue OS** |

Fix LeadScorer silent status promotion in a later sprint (not A0).

---

## 9. CRM UI: retain / rebuild / retire

**Recommendation for A1 decision packet:** **RETAIN source; do not treat as live shell until built & contracted.**

| Option | When |
|--------|------|
| Retain + mount | If A1 chooses SPA as Sales CRM SoT; add runner stage APIs; add nav; build dist in ops |
| Rebuild (Jinja CRM) | If Founder prefers single Jinja shell and thinner SPA |
| Retire SPA | Only if A1 proves Jinja+API covers CRM and SPA cost exceeds value |

**A0 does not choose** — A1 must ratify.

---

## 10. Smallest viable first Sales implementation slice (after A1)

**Not A0 work.** Candidate post-A1 slice:

> Sales OS boundary ADR + single CRM write path for **deal stage update** on the chosen UI surface + human gate for status/stage mutation — still no Marketing handoff, no external CRM sync.

---

## Cross-agent integration

| Topic | Disposition |
|-------|-------------|
| CRM ownership conflict | Documented; deferred to A1 ADR |
| Dual scorers | Security + domain agree PARTIAL |
| `/app` unmounted | Scout/Beacon agree |
| Marketing handoff missing | Hermes/Cipher agree |
| File conflicts this sprint | **0** (docs only under `docs/sales/`) |

---

## Go / no-go for A1

**READY FOR SALES A1**

A1 is architecture/domain boundary only. No Sales feature implementation until A1 completes and Founder accepts boundary ADR.
