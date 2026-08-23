# Founder OS Experience Architecture v1

**STATUS:** ARCHITECTURE ONLY  
**Sprint:** COS-ARCH-v1  
**Baseline:** `a7463e5`

---

## 1. Current screens (audit)

| Current name | Route | Template | Classification |
|--------------|-------|----------|----------------|
| Login | `/login` | `login.html` | OPERABLE |
| Command Center | `/command` | `founder_command.html` | OPERABLE — proposed **Home** |
| Demand & Contacts | `/demand` | `founder_demand.html` | OPERABLE — proposed **People** |
| Contact Revenue Workspace | `/contacts/{id}` | `founder_contact.html` | OPERABLE — **Person workspace** |
| Approval Inbox | `/pending-approvals` | `founder_approvals.html` | OPERABLE |
| Activity / Provenance | `/activity` | `founder_activity.html` | OPERABLE — label **Activity** |
| Revenue Workflow | `/operator` | `operator.html` | OPERABLE |
| Demand register | `/operator/demand/register` | operator | OPERABLE |
| Executive Cockpit | `/cockpit` | `cockpit.html` | LEGACY secondary |
| Sales | `/sales` | sales templates | OPERABLE thin |
| Marketing / Studio / Editorial / Publishing / SEO / Weeks | various | Content Ops | OPERABLE |
| Analytics | `/analytics` | analytics | PARTIAL |
| Pipeline (legacy page) | `/pipeline` | | LEGACY naming vs Deal pipeline |

Forbidden primary copy (UI-D1.5): SoT, MC04.5, TenantContext, AgentActionLog.

---

## 2. Recommended customer-facing terminology

| Avoid (engineering) | Use |
|---------------------|-----|
| Command Center | **Home** |
| Demand & Contacts | **People** (subtitle: demand + contacts) |
| Contact Revenue Workspace | **{Name}** — person workspace |
| Revenue Workflow | **Operator** (interim) → fold into Home |
| Provenance | **Activity** |
| Booking eligible | keep (outcome language) |
| Propose booking / worker | **Submit for approval** / **AI proposal** |
| requested_by | **AI proposal** / **Proposal** (already UI-D2 label) |
| Cockpit | retire from primary; “Legacy overview” if needed |

---

## 3. Experience architecture

### Global navigation

See [FOUNDER_OS_PRODUCT_HIERARCHY_v1.md](FOUNDER_OS_PRODUCT_HIERARCHY_v1.md). Org name in chrome (`founder-org-name`). No client tenant switcher.

### Home

Answers: what changed, what matters, what needs me, what AI proposed.  
Compose existing `build_command_center_snapshot` + eventually cockpit panels **into one read model** (do not keep two Homes).

### Domain navigation

Sales / Marketing / Revenue as secondary. Object-first.

### Object workspace

Person workspace is the gold pattern (reply, next action advisory, governed booking, deals list, follow-up).  
Company and Deal workspaces are **missing** — lists only.

### Search / command

Deferred palette; tenant-scoped. Keyboard: `/` later.

### Attention system

Pending approvals + operator-configured gating + booking/outreach proposals. Empty/error contracts exist for UI-D2 booking (`FOUNDER_OS_UI_D2_ERROR_EMPTY_STATE_CONTRACT.md`).

### Approval UX

Inbox; empty POST body; human session. Booking-specific copy is UI-D2 (supersedes D1 absence tests).

### AI Work UX

Show proposals as **proposals**. Never “AI booked a meeting.” Confirmation only after execution.

### Activity UX

Mix of CRM Activity + AgentActionLog is honest but dense. Group by person/time; hide worker ids behind “Details.”

### Notifications

No product notification SoT. Use in-page status + Approval count. Do not fake toasts as SoT.

### States

| State | Rule |
|-------|------|
| Empty | Honest (“No pending approvals”) |
| Loading | Server-render Jinja; JS fetch for availability only |
| Error | Fail closed (Outlook, no connector) |
| Stale | M4.5 slot no longer available — choose another |
| Unavailable | Tenant/contact isolation copy, not 500 |

### Mobile

Existing sidebar toggle. Booking panel must remain usable; no hover-only authority actions.

### Accessibility / i18n

See international UI requirements. Current: English, emoji in nav, limited a11y.

### Density / hierarchy

Founder screens: one primary action per card. Do not clone Content Studio density onto Home.

### AI vs human

Pills: Meeting interest (signal), Booking eligible (eligibility), Approval required (authority). Advisory next action labeled.

### Tenant visibility

Organization name only. Never credentials, hashes, or foreign org data.

---

## 4. Primary UX rule

Expose **outcomes and decisions**. Orchestration keys stay in Activity detail and docs.
