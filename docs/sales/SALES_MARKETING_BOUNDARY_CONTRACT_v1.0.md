# Sales ↔ Marketing Boundary Contract v1.0

**STATUS: FROZEN**  
**VERSION: v1.0**  
**Sprint:** SALES A1.5  
**Date:** 2026-08-13  
**ADR:** [Architecture_ADR_005.md](../architecture/Architecture_ADR_005.md)  
**Source:** [SALES_MARKETING_CONTRACT.md](SALES_MARKETING_CONTRACT.md) (A1)

---

## Freeze statement

**Sales ↔ Marketing Boundary: FROZEN**

Uses A1 terminology only: Marketing Signal → Marketing Qualification → **`QualifiedDemand`** → Sales Intake → Sales Qualification. Not a greenfield MQL/SQL product invent beyond A1.

---

## 1. Ownership before handoff

**Marketing OS owns:**

- Demand generation, campaigns, content, audience engagement  
- Marketing qualification (MQL semantics as A1)  
- Publish / editorial / website / SEO / social  

Marketing must **not** own CRM entity SoT.

---

## 2. Ownership after handoff

**Sales OS owns:**

- Accepted sales demand and subsequent sales lifecycle  
- Sales intake, sales qualification policy, engagement, pipeline ops  

Sales must **not** own editorial publish or campaign content lifecycle.

---

## 3. Handoff event: `QualifiedDemand`

Frozen minimum payload fields (A1): `demand_id`, `occurred_at`, `source`, `person`, optional `channel`, `company_hint`, `marketing_qualification`, `consent`, `content_attribution`.

Rules frozen:

- Idempotency on `demand_id`  
- Duplicate email → merge policy (no silent duplicate Contacts)  
- Rejection → `SalesDemandRejected` audit; no silent CRM pollution  
- No shared Marketing nurture ↔ Revenue CRM tables  

**Implementation status:** NOT_IMPLEMENTED (contract only).

---

## 4. Permitted / prohibited mutations

| Actor | Permitted | Prohibited |
|-------|-----------|------------|
| Marketing | Emit `QualifiedDemand`; own content/publish state | Write Revenue Contact/Deal tables directly from publish engines |
| Sales | Accept/reject intake; operate sales lifecycle | Mutate Editorial/Publishing/Website frozen contracts |
| Agents | Draft / recommend only | Bypass handoff; auto-create CRM without authority matrix |

---

## 5. Agent authority at boundary

Per [SALES_AGENT_AUTHORITY_CONTRACT_v1.0.md](SALES_AGENT_AUTHORITY_CONTRACT_v1.0.md): no autonomous Marketing→Sales CRM create; qualification decision HUMAN_ONLY; sends HUMAN_APPROVAL_REQUIRED.
