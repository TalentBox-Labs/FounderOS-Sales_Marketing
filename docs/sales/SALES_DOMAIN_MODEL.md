# Sales OS — Canonical Domain Model

**Sprint:** SALES A1  
**Date:** 2026-08-13  
**Status:** RESOLVED (conceptual) — physical schema unchanged  
**ADR:** [Architecture_ADR_004.md](../architecture/Architecture_ADR_004.md)

A0 finding **CONFLICTED** → A1 **RESOLVED** at the conceptual/governance layer. Physical tables remain as-is until future migration sprints.

---

## 1. Canonical conceptual model

```
Company ──< Contact ──< Deal ──< Activity
              │           │
              └── Pipeline ─┘
```

- **System of record:** Revenue OS (persisted entities).
- **Sales OS:** operates workflows and mutations through contracts/adapters — not a parallel CRM schema.

---

## 2. Entity disposition table

| Concept | Disposition | Canonical definition | Current implementation | Future mapping |
|---------|-------------|----------------------|------------------------|----------------|
| **Lead** | **CANONICAL** (alias) | Early-demand person record before/at qualification | `Contact` + `ContactStatus.LEAD/PROSPECT` + `LEAD_*` events | Keep alias; document in API contracts |
| **Contact** | **CANONICAL** | Person in CRM | `revenue_os.models.contact.Contact` | SoT remains Revenue |
| **Company** | **CANONICAL** | Organization/accountable org entity | `Company` table | SoT remains Revenue |
| **Account** | **CANONICAL** (alias) | Customer-success view of Company | CSM `AccountHealth` over `Company` | Alias only; no Account table |
| **Opportunity** | **CANONICAL** (alias) | Sales-process name for open commercial pursuit | **No table** — use `Deal` | Document `Opportunity ≡ Deal` in contracts |
| **Deal** | **CANONICAL** | Commercial pursuit with value/stage | `Deal` table | SoT Revenue; Sales operates stages |
| **Pipeline** | **CANONICAL** | Container for deals by type | `Pipeline` table | SoT Revenue |
| **PipelineStage** | **ADAPTER_REQUIRED** | Ordered stage in a pipeline | `DealStage` enum (truth) + `Pipeline.stages` CSV (**LEGACY**) | Future: relational stages or adapter normalizing enum↔CSV |
| **Activity** | **CANONICAL** | Engagement record | `Activity` table | SoT Revenue |
| **Task** | **CANONICAL** (subtype) | Scheduled work | `ActivityType.TASK` | No separate table |
| **Note** | **DUPLICATE** → **ADAPTER_REQUIRED** | Unstructured note | `Contact.notes` / `Company.notes` **and** `ActivityType.NOTE` | Prefer Activity NOTE for timeline; field notes LEGACY |
| **Source** | **CANONICAL** | Provenance enum | `ContactSource` | Marketing handoff sets `web_form` etc. |
| **Owner** | **ADAPTER_REQUIRED** | Assigned rep | `owner_id` UUID without User FK | Future FK + RBAC via Shared Platform |
| **Status** | **CANONICAL** | Contact lifecycle | `ContactStatus` enum | Sales proposes; human gate for promotion |
| **Value** | **CANONICAL** | Deal amount | `Deal.value` | Revenue field; Sales updates in pipeline ops |
| **Probability** | **CANONICAL** | Win likelihood | `Deal.probability` | Revenue field; may sync from stage rules |
| **CloseDate** | **CANONICAL** | Expected/actual close | `expected_close_date`, `closed_at` | Revenue fields |

---

## 3. Legacy / duplicate items (not deleted in A1)

| Item | Disposition | Action |
|------|-------------|--------|
| Dual API (`runner /api/v1/crm` vs JWT `/api/v1/contacts`) | **LEGACY** | REQUIRES_FUTURE_MIGRATION |
| Dual scorers (`scoring_service` vs `lead_scoring_service`) | **DUPLICATE** | REQUIRES_FUTURE_ADAPTER + governance |
| `DealStage` recruitment values on sales enum | **LEGACY** | REQUIRES_FUTURE_MIGRATION (split enum) |
| Marketing `SubscriberProfile` | **DEPRECATED_CANDIDATE** | DEFER — not Sales SoT |
| `MeetingActivity` schema without writers | **DEPRECATED_CANDIDATE** | DEFER retire |
| Content “pipeline” (`/pipeline` HTML) | **LEGACY** naming | RESOLVED_BY_CONTRACT (Marketing only) |

---

## 4. Relationships (canonical)

| From | To | Cardinality |
|------|-----|-------------|
| Company | Contact | 1:N |
| Company | Deal | 1:N |
| Contact | Deal | 1:N |
| Contact | Activity | 1:N |
| Deal | Activity | 1:N |
| Pipeline | Deal | 1:N |
| User | Contact/Deal.owner | 1:N (future enforced FK) |

---

## 5. Persistence (unchanged)

| Store | Role |
|-------|------|
| PostgreSQL | Entity SoT |
| ChromaDB | Search index (Shared infra) |
| JSON presets | Prospecting config |
| In-memory EventBus/workflows | **LEGACY** — not canonical SoT |

No new schemas in A1.

---

## Verdict

**Sales Domain Model: RESOLVED**

Conceptual model and aliases are ratified. Physical conflicts are mapped to migration/adapters — not resolved by deletion in A1.
