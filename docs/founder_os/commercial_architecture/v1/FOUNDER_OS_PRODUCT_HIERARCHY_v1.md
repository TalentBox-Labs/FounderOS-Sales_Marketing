# Founder OS Product Hierarchy v1

**STATUS:** ARCHITECTURE ONLY  
**Sprint:** COS-ARCH-v1  
**Baseline:** `a7463e5` (`founder-os-demo-runtime-v1.0`)

---

## 1. Audit of current navigation

Frozen UI-D1.5 primary nav (`templates/base.html`, [FOUNDER_OS_UI_D1_5_NAVIGATION_CONTRACT_v1.0.md](../../../ui/d1_5/FOUNDER_OS_UI_D1_5_NAVIGATION_CONTRACT_v1.0.md)):

| Label (current) | Route | Role today |
|-----------------|-------|------------|
| Command Center | `/command` | Attention + recommendations |
| Demand & Contacts | `/demand` | Demand list + contacts |
| Approvals | `/pending-approvals` | Human gate |
| Activity | `/activity` | Provenance |
| Revenue Workflow | `/operator` | Operator flow (QD / deal / outcome) |

Contact workspace `/contacts/{id}` is **not** a top-nav item (correct).

Secondary (Content Ops `<details>`): Dashboard `/`, legacy Cockpit `/cockpit`, Analytics, Content Calendar/Studio, Editorial, Publishing, SEO, Pipeline, Marketing `/marketing`, Sales `/sales`, MCP.

Also live: `/login`, `/operator/demand/register`, `/weeks`, `/seo/*`.

**Conflict:** UI1 cockpit IA recommended “Home / Executive Cockpit” as primary; UI-D1 shipped **Command Center** instead and left `/cockpit` as secondary. Two attention surfaces exist.

---

## 2. Conceptual model (not shipping nav)

The COS prompt’s full Sales / Marketing / Revenue trees are **information architecture catalogs**, not a 30-item sidebar.

Rules applied:

- Progressive disclosure
- Object workspaces over list-of-modules
- Founder priorities first
- Domain modules second
- Content engines third (already shipped, high cognitive load if primary)

---

## 3. Recommended canonical hierarchy

### Primary (always visible) — Founder loop

| Customer label | Route (near-term) | Replaces |
|----------------|-------------------|----------|
| **Home** | `/command` (evolve; do not fork a third cockpit) | “Command Center” |
| **People** | `/demand` then `/contacts/{id}` | “Demand & Contacts” |
| **Approvals** | `/pending-approvals` | unchanged |
| **AI Work** | section of Home + Approvals; later `/ai-work` | implicit worker lists |
| **Activity** | `/activity` | unchanged |

“Revenue Workflow” / Operator remains **reachable** (People empty-state, Home action, or Company → Tools) but should leave primary nav once Home covers QD accept + next actions. Until then keep `/operator` as primary to avoid stranding OF1.

**Recommended primary during COS-1 (compatibility):** Home, People, Approvals, Activity, Operator.

**Recommended primary after COS-5:** Home, People, Approvals, Activity. Operator absorbed.

### Domain (role/context) — not all founders, not all the time

| Domain | Customer label | Objects | Route today | Disposition |
|--------|----------------|---------|-------------|-------------|
| Sales | Sales | Pipeline, Accounts (`Company`), People (`Contact`), Opportunities (`Deal`) | `/sales` + contact workspace | Projection over Revenue SoT |
| Marketing | Marketing | Content, Campaigns, Channels, Intent | `/marketing`, studio, editorial, publishing, SEO | Keep engines; do not CRM-ize |
| Revenue | Revenue | Overview, Funnel, Forecast | `/analytics` + cockpit metrics | Thin; do not duplicate Deal SoT |

Meetings live on **Contact workspace** (UI-D2), not a top-level Meetings app.

Conversations / Engagement are **projections** of `Activity` + reply assessments, not new modules.

### Company (settings, not a fourth OS)

| Label | Meaning | Repository today |
|-------|---------|------------------|
| Founder profile | Preferences, not CRM | `User` + unstructured `preferences` |
| Workspace | Tenant | `Organization` |
| ICP / positioning / goals | Operating context | **Missing structured SoT** (Hermes `Goal` is planner, not company ARR) |
| Team | Membership | `OrganizationMembership` |
| Integrations | Connectors | `OrganizationIntegrationBinding` |
| Authority preferences | What AI may do | Scattered in contracts; **no settings UI** |

---

## 4. What must not enter primary nav

- Milestone codes, worker names, “provenance” as a product word (use Activity)
- Pipeline + Opportunities + Accounts as three equal top items (object workspaces instead)
- Legacy Cockpit **and** Home simultaneously as primary
- Content Studio / SEO as default founder path (disclose under Marketing)

---

## 5. Object workspace pattern

One canonical workspace per commercial object:

| Object | Workspace | SoT |
|--------|-----------|-----|
| Person | Contact revenue workspace | `Contact` |
| Account | Future Company workspace | `Company` |
| Opportunity | Future Deal workspace (Sales ops + Revenue values) | `Deal` |
| Demand | Operator demand + Demand list | `AgentActionLog` QualifiedDemand + Contact |
| Approval | Inbox item | `ApprovalRequest` |

Do not create a second “Lead workspace.”

---

## 6. Search / command

`search_service.py` exists. Product: global command palette later; COS-1 may keep in-page lists. Search must be tenant-scoped.

---

## 7. Hierarchy PASS criteria

- One Home
- People (contacts/demand) not duplicated as Leads + Contacts
- Approvals remain first-class (authority)
- Domain nav is secondary
- Company context is settings, not a fake CRM Company for the founder’s own firm mixed into prospect `Company` rows
