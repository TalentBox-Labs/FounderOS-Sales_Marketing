# Sales Domain Model Contract v1.0

**STATUS: FROZEN**  
**VERSION: v1.0**  
**Sprint:** SALES A1.5  
**Date:** 2026-08-13  
**ADR:** [Architecture_ADR_005.md](../architecture/Architecture_ADR_005.md)  
**Source:** [SALES_DOMAIN_MODEL.md](SALES_DOMAIN_MODEL.md) (A1)

**Does not:** migrate schemas, delete legacy models, or change runtime.

---

## Freeze statement

**Sales Domain Model Contract: FROZEN**

Conceptual model is canonical. Physical tables remain CURRENT IMPLEMENTATION until a future migration sprint.

---

## 1. Canonical entities

| Concept | Disposition | SoT owner | Identifier |
|---------|-------------|-----------|------------|
| Contact | CANONICAL | Revenue OS | UUID `contacts.id` |
| Company | CANONICAL | Revenue OS | UUID `companies.id` |
| Deal | CANONICAL | Revenue OS | UUID `deals.id` |
| Pipeline | CANONICAL | Revenue OS | UUID `pipelines.id` |
| Activity | CANONICAL | Revenue OS | UUID `activities.id` |
| Lead | CANONICAL **alias** | Revenue (`Contact` + status/events) | Same as Contact |
| Opportunity | CANONICAL **alias** | Revenue (`Deal`) | Same as Deal |
| Account | CANONICAL **alias** | Revenue (`Company` CSM view) | Same as Company |
| Task | CANONICAL subtype | `ActivityType.TASK` | Activity id |
| Source | CANONICAL | `ContactSource` | Enum |
| Owner | ADAPTER_REQUIRED | `owner_id` (no FK yet) | UUID |
| Status | CANONICAL | `ContactStatus` | Enum |
| Value / Probability / CloseDate | CANONICAL | Deal fields | — |
| PipelineStage | ADAPTER_REQUIRED | `DealStage` enum (truth); CSV LEGACY | Enum |

---

## 2. Relationships (frozen)

```
Company 1──* Contact
Company 1──* Deal
Contact 1──* Deal
Contact 1──* Activity
Deal    1──* Activity
Pipeline 1──* Deal
```

---

## 3. Lifecycle / state ownership

| State | Owner |
|-------|-------|
| Contact.status values | Revenue field; Sales proposes; human/policy gate for promotion |
| Deal.stage | Revenue field; Sales pipeline **ops** mutate via future adapter |
| Marketing nurture profiles | **Not** Sales SoT — DEFERRED / DEPRECATED_CANDIDATE |

---

## 4. Prohibited duplicate models

Future work must **not** introduce a second Contact/Deal/Company store under Sales OS.  
Aliases (Lead/Opportunity/Account) must not become parallel tables without ADR.

---

## 5. Legacy disposition (frozen classification)

| Item | Disposition |
|------|-------------|
| Dual runner CRM vs JWT APIs | ACCEPTED_LEGACY → REQUIRES_FUTURE_MIGRATION |
| Dual scorers | DUPLICATE → REQUIRES_FUTURE_ADAPTER |
| Note field + Activity NOTE | DUPLICATE → REQUIRES_FUTURE_ADAPTER |
| MeetingActivity writers absent | DEPRECATED_CANDIDATE → DEFERRED |
| Marketing SubscriberProfile | DEPRECATED_CANDIDATE → DEFERRED |

No deletions in A1.5.

---

## 6. Migration semantics

As mapped in [SALES_A1_MIGRATION_MAP.md](SALES_A1_MIGRATION_MAP.md). No migration executed by this freeze.
