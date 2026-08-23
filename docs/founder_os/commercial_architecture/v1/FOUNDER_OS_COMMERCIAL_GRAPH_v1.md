# Founder OS Commercial Graph v1

**STATUS:** ARCHITECTURE ONLY  
**Sprint:** COS-ARCH-v1  
**Baseline:** `a7463e5`

Physical models: `revenue_os/models/*`. Frozen aliases: [SALES_DOMAIN_MODEL_CONTRACT_v1.0.md](../../../sales/SALES_DOMAIN_MODEL_CONTRACT_v1.0.md).

---

## 1. Alias resolutions (binding)

| Concept | Canonical entity | Do not create |
|---------|------------------|---------------|
| Lead | `Contact` (`ContactStatus.LEAD` and events) | `leads` table |
| Opportunity | `Deal` | `opportunities` table |
| Account (CSM language) | `Company` | parallel account store |
| Tenant / workspace | `Organization` | using `Company` as tenant |
| Founder’s own firm (profile) | **New context object (proposed)** — not CRM `Company` | stuffing ICP into a prospect Company |
| Demand (pre-CRM) | QualifiedDemand **event** on `AgentActionLog` | Demand ORM duplicating Contact |
| Meeting (commercial) | `Activity` type MEETING + `MeetingActivity` + booking eligibility/state | treating calendar provider event as CRM SoT |
| Calendar event | Provider object behind connector | Founder OS inventing availability |
| Campaign (marketing) | Marketing engines + FS/content; not `OutreachSequence` | merging sales sequences into campaign SoT |
| Conversation | Projection of `Activity` + reply logs | chat SoT |
| RevenueEvent | `CommercialOutcome` log + `Deal` closed fields | premature finance ledger |
| Attribution | `content_attribution` on QD payload + analytics_depth (PARTIAL) | second CRM |

---

## 2. Entity catalog

### Organization

| Field | Value |
|-------|--------|
| Implementation | `revenue_os/models/organization.py` `Organization` |
| SoT | Shared Platform / SaaS S2 |
| Owner | Shared Platform (tenant), not Revenue CRM |
| Tenant key | `organizations.id` (is the tenant) |
| Identity | `slug` unique |
| Lifecycle | `active` / `suspended` |
| Relationships | 1—* `OrganizationMembership` |
| Status | LIVE |
| UI | Shell chrome org name; no client org switcher |
| Notes | Must not be confused with CRM `Company` |

### User

| Field | Value |
|-------|--------|
| Implementation | `revenue_os/models/user.py` |
| SoT | Identity (SaaS S1 REUSE_EXISTING_USER) |
| Owner | Shared Platform |
| Tenant key | none on User row (membership is the join) |
| Identity | `users.id`, unique `email` |
| Lifecycle | `is_active` |
| Relationships | *—* Organization via membership |
| Status | LIVE |
| UI | Login, operator.configured |
| Notes | `preferences` Text is unstructured — not Founder Profile |

### OrganizationMembership

| Field | Value |
|-------|--------|
| Implementation | `organization.py` |
| SoT | Tenant membership |
| Owner | Shared Platform |
| Tenant key | `organization_id` |
| Identity | `(user_id, organization_id)` unique |
| Lifecycle | `active` / `disabled`; roles owner/admin/member/viewer |
| Status | LIVE |
| UI | none dedicated |

### Company (CRM)

| Field | Value |
|-------|--------|
| Implementation | `contact.py` `Company` |
| SoT | Revenue OS CRM |
| Owner | Revenue OS |
| Tenant key | **none on model** (isolation via contacts/deals/org-scoped queries — debt) |
| Identity | `id`; `domain` unique nullable |
| Lifecycle | no status enum; industry optional |
| Relationships | 1—* Contact, Deal, Project |
| Status | LIVE |
| UI | Contact workspace field; no Company workspace |
| Notes | External account. Not the tenant. |

### Contact

| Field | Value |
|-------|--------|
| Implementation | `contact.py` `Contact` |
| SoT | Revenue OS CRM |
| Owner | Revenue OS; Sales **ops** consume |
| Tenant key | `organization_id` (nullable historically) |
| Identity | `contacts.id` |
| Lifecycle | `ContactStatus` lead → … customer |
| Relationships | N—1 Company; 1—* Deal, Activity |
| Status | LIVE |
| UI | `/contacts/{id}`, `/demand` |
| Notes | **Lead alias**. Status promotion is human/policy (LeadScorer auto-write is known gap). |

### Audience

| Field | Value |
|-------|--------|
| Implementation | **No ORM.** Marketing audience is engine/FS/SEO/social, not a graph node |
| Status | MISSING as commercial entity |
| Proposed | Derived segment over Contact + marketing signals; Marketing-owned definition; no second people store |

### Campaign

| Field | Value |
|-------|--------|
| Implementation | Marketing engines; `lead_nurturing.CampaignStatus` enum in code; no canonical `campaigns` table in models listing |
| Status | PARTIAL / engine-level |
| Owner | Marketing OS |
| Notes | Must not duplicate `OutreachSequence` |

### Lead

See Contact alias. Qualified marketing lead **before** CRM persist = QualifiedDemand event.

### Demand / QualifiedDemand

| Field | Value |
|-------|--------|
| Implementation | `qualified_demand_service.py`; persisted as `AgentActionLog` (`qualified_demand_handoff` / `_accepted` / `_rejected`) |
| SoT | Event log + resulting `Contact` |
| Owner | Marketing produces; Sales intake owns accept/reject |
| Tenant key | `AgentActionLog.organization_id` + Contact.organization_id |
| Identity | `demand_id` UUID (idempotent) |
| Lifecycle | handoff → accepted \| rejected |
| Status | LIVE (MC04) despite A1.5 doc saying NOT_IMPLEMENTED |
| UI | `/operator`, `/demand` |

### Conversation

Projection. No table.

### Activity

| Field | Value |
|-------|--------|
| Implementation | `activity.py` `Activity` + Email/Meeting subtypes |
| SoT | Revenue CRM timeline |
| Owner | Revenue OS |
| Tenant key | via Contact/Deal (weak) |
| Identity | `activities.id` |
| Lifecycle | type + status + timestamps |
| Status | LIVE; MeetingActivity writers historically thin |
| UI | Contact timeline / Activity screen (mixed with AgentActionLog) |

### AgentActionLog

| Field | Value |
|-------|--------|
| Implementation | `automation_state.py` |
| SoT | Automation / agent **audit** (not CRM timeline) |
| Owner | Shared/Automation consumed by all OS modules |
| Tenant key | `organization_id` nullable |
| Identity | string UUID `id` |
| Status | LIVE — also used as QD/CO event store |
| UI | `/activity` |
| Notes | **Justified dual** vs Activity: audit vs commercial timeline. Do not merge tables. Do not use as CRM SoT. |

### Meeting

Commercial meeting = `ActivityType.MEETING` + `MeetingActivity` + M4 booking state (eligibility/approval/calendar).  
Calendar event = provider ID on execution payload — **not** Founder OS SoT.

### Opportunity / Deal

| Field | Value |
|-------|--------|
| Implementation | `deal.py` `Deal` + `Pipeline` |
| SoT | Revenue OS |
| Owner | Revenue fields; Sales pipeline **ops** |
| Tenant key | not on Deal row (via contact/org — debt) |
| Identity | `deals.id` |
| Lifecycle | `DealStage` discovery … closed_won/lost (+ recruitment stages on same enum — conflict) |
| Status | LIVE |
| UI | Operator; not a first-class Deal workspace |

### RevenueEvent

No table. Approximate: `commercial_outcome_*` logs + Deal closed fields + `BillingRecord` (project finance — **separate**, must not silently become ARR SoT).

### Attribution

PARTIAL: QD `content_attribution`; `analytics_depth.py`; in-memory `AnalyticsEngine`. No canonical attribution entity.

### Goal

| Field | Value |
|-------|--------|
| Implementation | `goals.py` `Goal` / `GoalStep` table `hermes_goals` |
| SoT | Hermes planner |
| Owner | AI planner, **not** company strategy |
| Tenant key | **none** |
| Status | LIVE but wrong layer for Founder Company Goals |
| Proposed | Company Goals = new context (see Profile doc); Hermes Goal remains planner runtime |

### ApprovalRequest

| Field | Value |
|-------|--------|
| Implementation | `approvals.py` |
| SoT | Human gate |
| Owner | Shared governance; domains register action types |
| Tenant key | via payload / list filter (organization_id on list APIs) |
| Lifecycle | pending → approved \| rejected |
| Status | LIVE |
| UI | `/pending-approvals` |
| Authority | Client `requested_by`/`decided_by` must not create humanity |

### AutomationState / Workflow

| Concept | Implementation | Status |
|---------|----------------|--------|
| Heartbeat | `HeartbeatRun` | LIVE |
| Workflow ORM | `automation.py` `Workflow` | LEGACY / parallel |
| Revenue workflows | in-memory `WorkflowOrchestrator` keys M1–M4 | LIVE commercial |
| Proposed | Orchestrator keys + AgentActionLog are commercial workflow evidence; ORM Workflow is not a second revenue SoT |

### Project / Client / BillingRecord

Delivery/finance graph on `Company`. **Not** Deal. COS must not treat Project as Opportunity. HIGH overlap risk with CommercialOutcome.

### Content

| Implementation | Owner | Status |
|----------------|-------|--------|
| FS `tracker.csv` / weeks | Marketing Content Studio | SHIPPED |
| `ContentLibrary`, `Article`, `SocialPost` | DB content | PARTIAL duplicate vs FS |
| SEOKeyword | SEO engine | LIVE |

Canonical **website/editorial** SoT remains filesystem per Marketing frozen engines until an ADR. DB content is not silently promoted.

### Integrations

`ConnectorCredentialRecord`, `OrganizationIntegrationBinding` — Shared Platform; calendar credentials tenant-isolated (S4 / M4.5).

---

## 3. Canonical relationship sketch

```
Organization 1──* OrganizationMembership *──1 User
Organization ⋯ (scopes) Contact.organization_id, AgentActionLog.organization_id

Company 1──* Contact 1──* Deal
Company 1──* Deal
Contact 1──* Activity
Deal    1──* Activity
Pipeline 1──* Deal
Company 1──* Client 1──* Project

QualifiedDemand (log) ──creates/reuses── Contact
CommercialOutcome (log) ──references── Deal
ApprovalRequest ──governs── outreach / follow-up / book_meeting / …
Calendar provider event ──execution artifact── not CRM
```

---

## 4. Duplicate SoT policy

**Forbidden:** second Contact/Deal/Company under Sales or Marketing.

**Allowed dual (justified):** `Activity` (CRM timeline) vs `AgentActionLog` (audit/events).

**Debt duals:** listed in conflict audit (scorers, APIs, analytics stores, content FS vs DB, cockpit vs command).
