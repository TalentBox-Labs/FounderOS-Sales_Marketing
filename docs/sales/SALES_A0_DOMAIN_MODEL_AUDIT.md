# SALES A0 — Domain Model Audit (NOVA)

**Sprint:** SALES A0  
**Date:** 2026-08-13  
**Mode:** AUDIT ONLY — no new schemas

---

## Verdict

**Sales Domain Model: CONFLICTED**

Canonical runtime model is coherent enough to operate (**Company → Contact → Deal → Activity**), but naming, dual APIs, dual scorers, and Sales/Revenue ownership blur the domain.

---

## Concept inventory

| Concept | In code? | Representation | Persistence | Notes |
|---------|----------|----------------|-------------|-------|
| Lead | No table | `Contact` + `ContactStatus` / events | DB | Naming conflict |
| Contact | Yes | `Contact` | DB `contacts` | Canonical person |
| Account | No model | CSM language over `Company` | Computed | Alias conflict |
| Company | Yes | `Company` | DB `companies` | Canonical org |
| Opportunity | No | — | — | Use Deal |
| Deal | Yes | `Deal` | DB `deals` | value, probability, close dates |
| Pipeline | Yes | `Pipeline` | DB `pipelines` | `stages` as Text CSV |
| Pipeline Stage | No table | `DealStage` enum | Code + Deal.stage | CSV ignored by Deal |
| Activity | Yes | `Activity` | DB | NOTE/TASK subtypes |
| Task | Subtype | `ActivityType.TASK` | DB | |
| Note | Dual | Contact/Company Text + Activity NOTE | DB | Duplicate |
| Source | Enum | `ContactSource` | DB column | WEB_FORM unused by Marketing |
| Owner | Field | `owner_id` UUID | DB | No FK to User |
| Status | Enum | `ContactStatus` | DB | |
| Value | Field | `Deal.value` | DB | |
| Probability | Field | `Deal.probability` | DB | |
| Close Date | Fields | `expected_close_date`, `closed_at` | DB | |

---

## Relationships

```
Company 1──* Contact
Company 1──* Deal
Contact 1──* Deal
Contact 1──* Activity
Deal    1──* Activity
Pipeline 1──* Deal
User    ?── owner_id (logical only)
```

---

## Conflicts

1. Lead ≠ entity (status on Contact).  
2. Opportunity missing (Deal stands in).  
3. Account = Company (CSM).  
4. Dual scorers: `scoring_service.score_contact` vs `lead_scoring_service.score_contact` (auto status mutation).  
5. Dual APIs: runner `/api/v1/crm/*` (API key) vs JWT `/api/v1/contacts|deals|companies`.  
6. `DealStage` mixes sales + recruitment.  
7. Pipeline.stages CSV vs enum truth.  
8. “Pipeline” name collision with Marketing content pipeline.  
9. `owner_id` orphaned.  
10. Alembic revision empty; `create_all` is practical schema SoT.

---

## Persistence mechanisms

| Store | Sales use |
|-------|-----------|
| SQL (`DATABASE_URL`) | Primary CRM entities |
| ChromaDB | Search index |
| JSON `output/sales/prospecting_presets.json` | Prospecting presets |
| In-memory | EventBus, WorkflowEngine runtime, nurture profiles |
| Google Sheets | Content ops — **not** Sales CRM |

**Sales Domain Model: CONFLICTED**
