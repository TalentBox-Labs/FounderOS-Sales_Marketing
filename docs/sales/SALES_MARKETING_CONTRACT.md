# Sales ↔ Marketing Contract

**Sprint:** SALES A1  
**Date:** 2026-08-13  
**Status:** DEFINED (governance) — **not implemented**  
**ADR:** [Architecture_ADR_004.md](../architecture/Architecture_ADR_004.md)

Resolves A0: **Sales ↔ Marketing Boundary: PARTIAL** → **DEFINED**.

---

## 1. Boundary rule

| OS | Owns |
|----|------|
| **Marketing OS** | Demand generation, campaigns, content, audience engagement, **marketing qualification** (MQL semantics), publish/editorial/website/SEO/social |
| **Sales OS** | **Accepted sales demand** and subsequent sales lifecycle (SQL intake, sales qualification, engagement, pipeline ops) |

Marketing must **not** own CRM entity SoT. Sales must **not** own editorial publish or campaign content lifecycle.

---

## 2. Handoff flow (conceptual)

```
Marketing Signal
    → Marketing Qualification (MQL)
    → QualifiedDemand (contract payload)
    → Sales Intake
    → Sales Qualification (SQL policy)
    → Revenue Contact/Company records (via adapter)
```

No shared persistence tables between Marketing nurture profiles and Revenue CRM.

---

## 3. Contract: `QualifiedDemand` (future event/API)

### Payload (minimum)

| Field | Required | Semantics |
|-------|----------|-----------|
| `demand_id` | Yes | Idempotency key (UUID) |
| `occurred_at` | Yes | ISO timestamp |
| `source` | Yes | e.g. `web_form`, `campaign`, `social`, `event` |
| `channel` | No | Campaign/content reference (opaque ID) |
| `person` | Yes | `{ email?, name?, phone?, linkedin_url? }` |
| `company_hint` | No | `{ name?, domain? }` |
| `marketing_qualification` | No | `{ score?, tier?, notes? }` — Marketing-owned semantics |
| `consent` | Conditional | `{ marketing_opt_in?, privacy_basis? }` where applicable |
| `content_attribution` | No | UTM / content_id / landing_path |
| `reject_reason` | No | If Marketing pre-rejects |

### Identity / reference semantics

- Sales intake creates or matches **Revenue** `Contact` / `Company` — not a Marketing row.
- `demand_id` stored on Contact metadata or intake audit log for idempotency.
- Duplicate email: **merge policy** — update existing Contact if same email; never duplicate silently.

### Ownership transfer

- At successful Sales intake accept: Marketing **stops** owning lifecycle decisions; Sales owns engagement workflow.
- Marketing retains read-only attribution on Contact.source / audit.

### Rejection behavior

- Sales may reject demand (spam, ICP mismatch) → audit event `SalesDemandRejected`; no CRM create or soft-create with `CHURNED`/archived flag per future policy.

### Idempotency

- Same `demand_id` → same intake outcome (201 existing / 200 noop).

---

## 4. Transport (future — not A1)

Preferred: **async event** on Shared Platform event bus (`marketing.qualified_demand.v1`).  
Alternative: **POST** `/api/v1/sales/intake/demand` (Sales OS facade).

Marketing OS **must not** write directly to `revenue_os.models` from publish engines.

---

## 5. Current repository state

| Item | Status |
|------|--------|
| `ContactSource.WEB_FORM` | Enum exists; **no Marketing writer** |
| `lead_nurturing.SubscriberProfile` | In-memory; **not wired** |
| Editorial / Publishing gates | **Frozen** — unrelated to Sales intake |

Implementation: **NOT_IMPLEMENTED** — contract only.

---

## 6. Explicit non-goals

- Marketing campaign sequences ≠ Sales outreach sequences.
- Editorial approval ≠ Sales actions.
- Website form submission handler — future Marketing or Shared webhook → contract emitter.

---

## Verdict

**Sales ↔ Marketing Boundary: DEFINED**
