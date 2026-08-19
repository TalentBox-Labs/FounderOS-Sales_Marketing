# Founder OS Architecture Conflict Audit v1

**STATUS:** AUDIT  
**Sprint:** COS-ARCH-v1  
**Baseline:** `a7463e5`  
**Rule:** Tests passing ≠ debt gone.

Severity: CRITICAL (can corrupt SoT/authority/tenant) · HIGH (duplicate or wrong owner) · MEDIUM (UX/scale/docs) · LOW.

---

## CRITICAL (4)

| ID | Issue | Evidence |
|----|-------|----------|
| C1 | Physical package `revenue_os/` hosts Sales, Marketing-adjacent, Founder, SaaS — future agents treat folder as Revenue ownership | ADR-004 ACCEPTED_LEGACY; code layout |
| C2 | No attested company/ICP SoT; Hermes `Goal` + copilot inference can be mistaken for company truth | `goals.py` `hermes_goals`; no FounderWorkspaceContext |
| C3 | Dual app identity: `runner_api` cookie vs `revenue_os.main` JWT vs `RUNNER_API_KEY` | SaaS S0/S1 docs; two entrypoints |
| C4 | `Deal` (and historically some CRM rows) lack first-class `organization_id`; isolation depends on joins/guards | `deal.py`; S3 mutation guards exist but schema incomplete |

---

## HIGH (8)

| ID | Issue | Evidence |
|----|-------|----------|
| H1 | Dual lead scorers | Sales domain contract: DUPLICATE scorers |
| H2 | Dual CRM API stacks (runner CRM vs JWT) | ADR-004 ACCEPTED_LEGACY |
| H3 | Dual analytics: in-memory `AnalyticsEngine` vs `AnalyticsMetricRecord` | `analytics/` vs `automation_state.py`; DEMO-D1.1 metrics path |
| H4 | Dual workflow: ORM `Workflow` vs in-memory `WorkflowOrchestrator` M1–M4 | `automation.py` vs `agents/orchestration.py` |
| H5 | Content SoT split: FS tracker vs `ContentLibrary`/`Article` | Marketing v2.2 FS; `content.py` |
| H6 | Two Founder attention surfaces: `/command` vs `/cockpit` | UI-D1 vs UI2.5 |
| H7 | Delivery finance (`Client`/`Project`/`BillingRecord`) vs `Deal`/`CommercialOutcome` | `project.py` vs MC06 |
| H8 | LeadScorer / automation may write `Contact.status` vs human promotion policy | Sales revenue boundary; A4.5 |

---

## MEDIUM (10)

| ID | Issue | Evidence |
|----|-------|----------|
| M1 | A1.5 Marketing contract still says QD `NOT_IMPLEMENTED` | contract vs `qualified_demand_service.py` |
| M2 | Same for CommercialOutcome in A1.5 vs MC06 service | contract vs `commercial_outcome_service.py` |
| M3 | MDG0 “not multi-tenant” vs S1–S4 tenancy | product vs saas docs |
| M4 | `DealStage` mixes sales and recruitment | `deal.py` enum |
| M5 | `User.role` vs membership role | `user.py` vs `OrganizationMembership.role` |
| M6 | Activity screen mixes CRM `Activity` and `AgentActionLog` | founder activity RM |
| M7 | UI-D1.5 frozen tests vs UI-D2 booking presence | SUPERSEDED_NEGATIVE_SCOPE; not a product bug |
| M8 | Demo seed shortcuts (company string historically; SQLite UUID) | DEMO-D1.x; must not become graph law |
| M9 | `/pipeline` and `/weeks` legacy vs commercial IA | `ui.py` routes |
| M10 | No Account/Deal workspaces; Sales `/sales` thin | templates |

---

## LOW (selected)

| ID | Issue |
|----|-------|
| L1 | Emoji primary nav vs a11y |
| L2 | Architecture v2.2 CS/Ops/Knowledge unused in Founder nav |
| L3 | `MeetingActivity` writers historically thin |
| L4 | Search service not in Founder shell |
| L5 | Celery/Redis partial on some hosts (S0) |

---

## Duplicate SoT clusters (8)

Counted as **unjustified or debt duals** (not the justified Activity vs AgentActionLog split):

1. Dual scorers  
2. Dual CRM APIs  
3. Dual analytics stores  
4. Dual workflow engines  
5. Content FS vs DB  
6. Cockpit vs Command attention  
7. Project/Client billing vs Deal/CO  
8. Candidate (recruitment) vs Contact (people)

Justified dual (not counted): `Activity` vs `AgentActionLog`.

---

## Cross-domain conflicts (12)

1. Sales ops vs Revenue CRM SoT (folder vs ADR)  
2. Marketing vs Sales QD (docs vs code)  
3. Lead vs Contact alias discipline  
4. Opportunity vs Deal alias discipline  
5. Company vs Organization  
6. Campaign engines vs `OutreachSequence`  
7. Hermes Goal vs company goals  
8. Meeting Activity vs calendar event  
9. Reply interest vs qualification write  
10. Founder UI vs Marketing FS SoT  
11. Product packaging vs tenant isolation  
12. Recruitment pipeline stages on sales Deal enum  

---

## Template / backend drift

- UI-D2 templates contain governed booking; D1 freeze asserted absence — **attested supersession**, not silent drift to undo.  
- `attach_safe_booking` wraps snapshots so patched tests still see booking chrome.  
- Templates must not gain Deal.stage machines.

---

## Direct DB coupling

Founder read models use `SessionLocal` + ORM. Acceptable if tenant filters applied. Risk: any new screen querying unscoped `Deal`/`Company`.

---

## Scalability

In-memory orchestrator and analytics do not survive multi-instance without shared store. Fine for hosted single deployment; not SaaS scale.

---

## Counts (report)

| Class | Count |
|-------|-------|
| CRITICAL | 4 |
| HIGH | 8 |
| MEDIUM | 10 |
| Duplicate SoT clusters | 8 |
| Cross-domain conflicts | 12 |
