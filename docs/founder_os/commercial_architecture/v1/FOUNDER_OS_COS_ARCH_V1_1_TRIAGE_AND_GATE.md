# Founder OS COS-ARCH-v1.1 — Critical Risk Triage and COS-1 Gate

**STATUS:** ARCHITECTURE REVIEW ONLY  
**Sprint:** COS-ARCH-v1.1  
**Branch:** `founder-os-architecture-v1`  
**HEAD / baseline:** `a7463e5e6bb8785749c6f5faab972e75dccc6b5f`  
**Parent pack:** `docs/founder_os/commercial_architecture/v1/`  
**Nature:** Documentation. No production code, tests, or commit.

Correction vs v1 audit C4: `Contact.organization_id` and `Deal.organization_id` **exist** (`contact.py`, `deal.py`) as **nullable**. The live risk is null/legacy rows and **`Company` having no tenant column**, not a missing Deal column.

---

## CRITICAL triage (4/4)

### C1 — `revenue_os/` package ≠ Revenue OS ownership

| | |
|--|--|
| Files / entities | Physical tree `revenue_os/models/*`, `revenue_os/services/*` (includes `qualified_demand_service.py`, `founder_ui_read_model.py`, `tenant_context.py`, `lead_scoring_service.py`). Law: `docs/architecture/Architecture_ADR_004.md`, `docs/sales/SALES_OS_ARCHITECTURE_BASELINE_v1.0.md` |
| Domain | Shared layout affecting Founder / Sales / Marketing-adjacent / Revenue |
| COS-1 | **CONTAINED** |
| Why | COS-1 uses existing services in place. Extracting `sales_os/` would be a migration, not a spine fix. Risk is **agent mis-ownership**, not runtime. |
| Decision | Folder is ACCEPTED_LEGACY. Ownership follows ADR-004/005, not path prefix. COS-1 PRs must name domain owner in the sprint, not “Revenue OS” because the file lives under `revenue_os/`. |
| Implementation | Later (package extract). Not now. |
| Frozen contracts | ADR-004/005 — **do not amend** for a rename. |
| UI terminology | No. Users never see package names. |

### C2 — No attested company/ICP SoT vs Hermes Goal / copilot

| | |
|--|--|
| Files / entities | `revenue_os/models/goals.py` (`hermes_goals`, `Goal`); `revenue_os/services/hermes_planner.py` (`goal_created`); `revenue_os/services/copilot.py`; `User.preferences` unstructured; **no** `FounderWorkspaceContext` |
| Domain | Founder OS context vs AI Platform planner |
| COS-1 | **CONTAINED** |
| Why | COS-1 spine does not require ICP persistence. Danger is COS-1 **writing** copilot/Hermes output into “company truth” or labeling Hermes Goal as ARR. |
| Decision | COS-1 company context = **display** `Organization.name` + signed-in `User` only. Hermes `Goal` is planner runtime, not Company Goals. AI inference must be labeled derived (existing “advisory only” pattern). |
| Implementation | Now: **none** (forbid new SoT). Later: attested context ADR. |
| Frozen contracts | None unfrozen. Do not treat Hermes goals as Sales/Revenue SoT. |
| UI terminology | Yes if copy says “Goals” meaning Hermes. COS-1 must not rename Command metrics to “Company goals.” |

### C3 — Dual identity: runner cookie vs `revenue_os.main` JWT vs API key

| | |
|--|--|
| Files / entities | `runner_api.py` (primary); `runner_api_routers/identity.py`; `revenue_os/services/identity_context.py`; `revenue_os/main.py` (JWT FastAPI “Revenue OS”); `RUNNER_API_KEY`; docs `docs/saas/s0/SAAS_CURRENT_ARCHITECTURE.md`, `docs/saas/s1/S1_IDENTITY_ARCHITECTURE.md` |
| Domain | Shared platform |
| COS-1 | **CONTAINED** |
| Why | Founder UI-D1/D2 already uses `runner_api`. COS-1 fails if it adds a second login or calls `revenue_os.main` as the product shell. |
| Decision | **Founder OS HTTP SoT for COS-1 = `uvicorn runner_api:app` only.** `revenue_os.main` is out-of-scope legacy API. `RUNNER_API_KEY` remains SERVICE, never HUMAN. |
| Implementation | Not now. Later: retire or wrap JWT app. |
| Frozen contracts | S1 identity — preserve. |
| UI terminology | Login is already Founder login; do not introduce “Revenue OS app” as a second product. |

### C4 — Tenant columns nullable; Company unscoped

| | |
|--|--|
| Files / entities | `Contact.organization_id` nullable (`contact.py`); `Deal.organization_id` nullable (`deal.py`); **`Company` has no `organization_id`**; guards: `tenant_scoped_access.py` (`get_contact_for_tenant`, `apply_deal_org_filter`, `_org_match` False on null); `tenant_mutation_guard.py`; founder RM `build_contact_workspace_snapshot` filters deals by `Deal.organization_id` when org present |
| Domain | Shared tenant + Revenue CRM |
| COS-1 | **CONTAINED** (becomes BLOCKER if COS-1 adds Account/global Deal/Company lists) |
| Why | Person workspace already uses `get_contact_for_tenant`. Null org_id is fail-closed for activity visibility. COS-1 does **not** need a Company tenant migration. |
| Decision | COS-1 reads **only** existing org-scoped founder read models. No new unscoped `db.query(Company)` / `db.query(Deal)`. Schema backfill + Company.tenant key = COS-3. |
| Implementation | Later (nullable backfill, Company org_id). Not a COS-1 schema sprint. |
| Frozen contracts | S2–S4 tenant tests — do not weaken filters. |
| UI terminology | No, unless COS-1 ships “Accounts” as a global company list. |

---

## HIGH triage (8/8)

### H1 — Dual scorers

| | |
|--|--|
| Files | `revenue_os/services/lead_scoring_service.py` (`LeadScorer`, A4 path); `revenue_os/services/scoring_service.py` (writes `contact.lead_score`; JWT/Celery-era). Contract: `docs/sales/a4_5/LEADSCORER_CONTACT_STATUS_CONTRACT_v1.0.md` |
| Domain | Sales policy + Revenue `Contact.lead_score` field |
| COS-1 | **CONTAINED** |
| Why | UI displays `Contact.lead_score`. COS-1 must not invoke both engines or invent a third. |
| Decision | COS-1 **read** `lead_score` from Contact. Authoritative scorer for Founder/runner remains `lead_scoring_service` (A4.5). `scoring_service.py` is legacy path — do not wire into Founder screens. |
| Implementation | Unify later. |
| Frozen | A4.5 — preserve score vs status split. |
| UI | “Lead score” is a field, not a Lead entity. |

### H2 — Dual CRM API stacks

| | |
|--|--|
| Files | `runner_api_routers/crm.py` + `runner_api.py` include; `revenue_os/main.py` + `revenue_os/api/v1` |
| Domain | Revenue SoT, Sales/Founder facades |
| COS-1 | **CONTAINED** |
| Why | Founder mutations already go through runner revenue/CRM/orchestration routers. |
| Decision | COS-1 APIs = runner routes already used by UI-D1/D2 (`/api/v1/revenue/...`, approvals, operator). No new JWT-app screens. |
| Implementation | Facade merge later. |
| Frozen | ADR-004 ACCEPTED_LEGACY. |
| UI | No. |

### H3 — Dual analytics stores

| | |
|--|--|
| Files | `revenue_os/analytics/` (`AnalyticsEngine` in-memory); `AnalyticsMetricRecord` in `automation_state.py`; `runner_api_routers` analytics; `/analytics` |
| Domain | Revenue intelligence (thin) |
| COS-1 | **DEFERRED** |
| Why | COS-1 slice does not ship Revenue Overview/forecast. `/analytics` stays secondary, unused as ARR SoT. |
| Decision | Templates must not invent ARR from either store. Merge stores in COS-4. |
| Implementation | Later. |
| Frozen | None blocking COS-1. |
| UI | Do not label analytics as “Revenue OS source of truth.” |

### H4 — Dual workflow engines

| | |
|--|--|
| Files | `revenue_os/models/automation.py` (`Workflow`, `WorkflowExecution`); `revenue_os/agents/orchestration.py` (`WorkflowOrchestrator`, keys `rev_orch_research_to_outreach` … `rev_orch_booking_to_meeting`) |
| Domain | Automation Platform vs Revenue/Sales orch |
| COS-1 | **CONTAINED** |
| Why | Live commercial spine is M1–M4 orchestrator + `AgentActionLog`, not ORM Workflow. |
| Decision | COS-1 must not add UI that starts `models.automation.Workflow` as the person journey. Operator/contact actions stay M1–M4. |
| Implementation | Retire or adapter later. |
| Frozen | M1.5–M4.5. |
| UI | Avoid “Revenue Workflow” as a second product; Operator is interim label (hierarchy pack). |

### H5 — Content FS vs DB

| | |
|--|--|
| Files | FS `tracker.csv` / `input/{week}/` (Marketing v2.2); `revenue_os/models/content.py` (`ContentLibrary`, `Article`, `SocialPost`); `runner_api_routers/ui.py` `/content-studio`, `/weeks` |
| Domain | Marketing OS |
| COS-1 | **DEFERRED** |
| Why | COS-1 does not traverse Content Studio as the commercial spine. |
| Decision | Marketing SoT for engines remains FS until a content ADR. COS-1 must not copy articles into Contact. |
| Implementation | Later. |
| Frozen | Marketing OS v2.2 engine baselines. |
| UI | Keep Content Ops secondary. |

### H6 — `/command` vs `/cockpit`

| | |
|--|--|
| Files | `founder_ui_read_model.build_command_center_snapshot`; `templates/founder_command.html`; `cockpit_read_model.py`; `templates/cockpit.html`; routes in `runner_api_routers/ui.py`; UI-D1.5 nav vs UI2.5 |
| Domain | Founder OS |
| COS-1 | **CONTAINED** |
| Why | Two Homes would split attention. COS-1 can keep both **routes** if only `/command` is primary. |
| Decision | COS-1 **Home = `/command`**. `/cockpit` remains secondary; **no new cockpit features**. Merge read models in COS-5. |
| Implementation | Copy/nav only in COS-1 if desired; no merge sprint required to start. |
| Frozen | UI-D1.5 primary nav still says “Command Center” — rename to Home is **copy**, may need nav-contract unfreeze if tests assert the string. Prefer keep “Command Center” label in COS-1 to avoid frozen nav churn. |
| UI | Terminology depends on whether COS-1 renames. **Recommendation: keep frozen label Command Center in COS-1.** |

### H7 — `Client`/`Project`/`BillingRecord` vs `Deal`/`CommercialOutcome`

| | |
|--|--|
| Files | `revenue_os/models/project.py`; `commercial_outcome_service.py` (`commercial_outcome_*` on `AgentActionLog`); `Deal` |
| Domain | Revenue (CRM vs delivery finance) |
| COS-1 | **CONTAINED** |
| Why | Operator CO path is Deal-based. COS-1 must not show Project as Opportunity. |
| Decision | Opportunity = `Deal` only. Project/Client out of COS-1 UI. |
| Implementation | Boundary docs later; no schema now. |
| Frozen | MC06.5 / Sales↔Revenue contract. |
| UI | Never label Project as a deal. |

### H8 — Contact.status vs LeadScorer

| | |
|--|--|
| Files | `lead_scoring_service.py` (`score_contact` score-only; `apply_contact_status_update`; `suggest_status_from_score`); runner `PATCH .../crm/contacts/{id}/status`; frozen `LEADSCORER_CONTACT_STATUS_CONTRACT_v1.0.md`; `scoring_service.py` does **not** set status (score only) |
| Domain | Sales qualification policy + Revenue Contact field |
| COS-1 | **CONTAINED** |
| Why | A4.5 already: machine recommends, human PATCHes status. Contact workspace labels next action advisory (UI-D1.5). M3 meeting interest must not write QUALIFIED. |
| Decision | COS-1 **must not** auto-promote status from score, reply, or booking eligibility. Do not add template/JS status writes. |
| Implementation | Not now if COS-1 stays on existing buttons. |
| Frozen | A4.5, M3.5 qualification boundary, UI-D1.5 human authority. |
| UI | “Booking eligible” / “Recommended” must stay advisory. |

---

## Duplicate SoT clusters → gate class

| Cluster | Maps to | COS-1 |
|---------|---------|-------|
| Dual scorers | H1 | CONTAINED |
| Dual CRM APIs | H2 | CONTAINED |
| Dual analytics | H3 | DEFERRED |
| Dual workflow engines | H4 | CONTAINED |
| Content FS vs DB | H5 | DEFERRED |
| Cockpit vs Command | H6 | CONTAINED |
| Project/Client vs Deal/CO | H7 | CONTAINED |
| Candidate vs Contact | not in HIGH; `recruitment.py` `Candidate` | **DEFERRED** (COS-1 people = `Contact` only) |

---

## Cross-domain conflicts → gate class

| Conflict | COS-1 |
|----------|-------|
| Folder vs ADR ownership | C1 CONTAINED |
| QD docs vs MC04 code | **DEFERRED** doc hygiene (M1); runtime LIVE — use the service |
| Lead vs Contact | Frozen ALIAS below |
| Opportunity vs Deal | Frozen ALIAS below |
| Company vs Organization | Frozen EXISTING below |
| Campaign vs OutreachSequence | DEFERRED (H5/COS-2) |
| Hermes Goal vs company goals | C2 CONTAINED |
| Meeting Activity vs calendar event | Frozen below |
| Reply vs qualification write | H8 CONTAINED |
| Founder UI vs Marketing FS | H5 DEFERRED |
| Product packaging vs tenant | C3/C4 CONTAINED |
| Recruitment stages on `DealStage` | DEFERRED (M4); COS-1 must not use recruitment stages in Founder copy |

---

## A. COS-1 MUST-FIX LIST

Architecture/scope only. **No production schema required before COS-1 starts.**

1. **Adopt this v1.1 entity freeze** (section D). No `leads` / `opportunities` / `demands` tables.  
2. **Bound the HTTP product** to `runner_api:app` Founder screens already in the spine (`/command`, `/demand`, `/contacts/{id}`, `/pending-approvals`, `/activity`, `/operator`).  
3. **Bound read/write paths** to existing org-scoped founder/operator/orchestration services — no new unscoped Company/Deal queries.  
4. **Bound Home** to `/command`; do not merge or feature `/cockpit` in COS-1.  
5. **Bound company context** to Organization + User display; do not persist copilot/Hermes as ICP/ARR.  
6. **Preserve authority:** no client `requested_by`/`decided_by`; no auto `Contact.status`; no booking execution without approval (existing M4.5/UI-D2).  
7. **Do not modify frozen tests** (UI-D1.5 / INT-D2 / A3.5 / A4.5 / M*.5). Prefer keep nav label **Command Center** to avoid UI-D1.5 string freeze.

---

## B. COS-1 CONTAINMENT LIST

C1, C2, C3, C4, H1, H2, H4, H6, H7, H8 — remain in tree, explicitly out of COS-1 mutation scope except copy/wiring on the existing spine.

---

## C. POST-COS-1 DEBT LIST

| Item | When |
|------|------|
| H3 analytics dual store | COS-4 |
| H5 content FS vs DB | Marketing ADR / COS-2+ |
| Candidate vs Contact | Out of commercial COS until CS/recruitment |
| Company.organization_id + null backfill | COS-3 |
| Package extract `sales_os/` | After C1 ADR |
| JWT app retirement | After C3 ADR |
| Cockpit+Command merge | COS-5 |
| DealStage recruitment split | later ADR |
| Stale A1.5 NOT_IMPLEMENTED wording | doc-only anytime |

---

## D. Canonical entity decisions (COS-1 freeze)

| Entity | COS-1 class | Meaning |
|--------|-------------|---------|
| Organization | **EXISTING CANONICAL** | Tenant. `organization.py`. Not CRM. |
| Company | **EXISTING CANONICAL** | External account. `contact.py` `Company`. Not tenant. No Account table. |
| Contact | **EXISTING CANONICAL** | Person SoT. `contacts`. |
| QualifiedDemand | **EXISTING CANONICAL** (event, not table) | `qualified_demand_*` on `AgentActionLog` + resulting Contact. |
| Deal | **EXISTING CANONICAL** | Opportunity record. `deals`. |
| Opportunity | **ALIAS** | UI/sales language for `Deal`. |
| Lead | **ALIAS** | Early `Contact` (+ status/events). |
| CommercialOutcome | **EXISTING CANONICAL** (event, not table) | `commercial_outcome_*` logs; does not replace Deal. |
| ApprovalRequest | **EXISTING CANONICAL** | Human gate. `approvals.py`. |
| AgentActionLog | **EXISTING CANONICAL** | Audit/event log. Not CRM timeline. |
| Activity | **EXISTING CANONICAL** | CRM timeline. `activity.py`. |
| Meeting | **EXISTING CANONICAL** (commercial) + **DERIVED** (calendar) | Commercial: `ActivityType.MEETING` + `MeetingActivity` + M4 booking state. Calendar provider event: execution artifact, not a second CRM SoT. |

**NOT YET INTRODUCED (forbidden in COS-1):** Audience, Campaign graph table, FounderWorkspaceContext schema, RevenueEvent ledger, Lead table, Opportunity table.

Remaining ambiguities after this freeze: **0** for the twelve named entities.

---

## E. GO/NO-GO rationale

- Authority path for the spine is already frozen and tested (approvals, A4.5, M3.5, M4.5, UI-D2).  
- Tenant path for the spine is already in founder read models + S2–S4 guards.  
- No CRITICAL item requires a migration **if COS-1 stays inside the existing person journey**.  
- NO-GO would apply if COS-1 were redefined as ICP/Audience/Company workspaces or a second app shell.

**Verdict: CONDITIONAL GO** — proceed only under section A bounds.
