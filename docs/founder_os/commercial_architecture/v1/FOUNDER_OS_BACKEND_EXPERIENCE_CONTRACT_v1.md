# Founder OS Backend Experience Contract v1

**STATUS:** ARCHITECTURE ONLY  
**Sprint:** COS-ARCH-v1  
**Baseline:** `a7463e5`

UI is never SoT. Templates must not invent lifecycle. Client must not infer authority.

---

## UI law (repeat)

Must not: become SoT; fabricate commercial state; infer authority client-side; bypass orchestration; mutate CRM/calendar directly; duplicate business logic; create new states in Jinja.

---

## Primary screens

### Home (`/command`)

| Field | Contract |
|-------|----------|
| Read model | `build_command_center_snapshot` |
| Source | `founder_ui_read_model.py` |
| API | HTML GET `/command` |
| Context | `TenantContext` / org_id |
| Actions | links to People, Approvals, Operator; no CRM writes |
| Authority | read |
| Tenant | org-scoped query |
| Freshness | request-time |
| Revalidation | n/a |
| Loading | full page |
| Empty | snapshot empty panels |
| Error | unavailable state |
| Provenance | none required on cards |
| Derived vs authoritative | **all derived** from CRM + logs |
| Sufficiency | **PARTIAL** — overlaps `/cockpit`; booking pending list added in UI-D2 era |

### People (`/demand`)

| Field | Contract |
|-------|----------|
| Read model | `build_demand_contacts_snapshot` |
| API | GET `/demand` |
| Actions | open contact; no status writes |
| Authority | read |
| Sufficiency | **PARTIAL** — not a full audience/lead marketing list |

### Person workspace (`/contacts/{id}`)

| Field | Contract |
|-------|----------|
| Read model | `build_contact_workspace_snapshot` + `attach_safe_booking` |
| API | GET `/contacts/{id}` |
| Actions | research-to-outreach, follow-up propose, load availability, submit booking proposal — **canonical JSON APIs** |
| Authority | `operator.configured`; approvals for send/book; empty JSON on approve |
| Tenant | 422/isolation if wrong org |
| Freshness | eligibility at request; slots at availability GET |
| Revalidation | M4.5 on approve/execute |
| Loading | page + JS availability |
| Empty | no reply / no deals |
| Error | booking ERROR / no connector / outlook |
| Provenance | Activity + logs |
| Authoritative | Contact, Deal rows |
| Derived | reply assessment, booking `ui_state`, recommendations (advisory) |
| Sufficiency | **LIVE for COS-1 spine**; missing Company/Deal child workspaces |

### Approvals (`/pending-approvals`)

| Field | Contract |
|-------|----------|
| Read model | `build_approvals_snapshot` (+ booking_display enrich) |
| API | GET HTML; POST `/api/v1/approvals/{id}/approve\|reject` |
| Actions | approve/reject |
| Authority | session human; ignore client decided_by when tenant present |
| Sufficiency | **LIVE** |

### Activity (`/activity`)

| Field | Contract |
|-------|----------|
| Read model | `build_activity_snapshot` |
| API | GET `/activity` |
| Sufficiency | **LIVE**; mixed log types |

### Operator (`/operator`)

| Field | Contract |
|-------|----------|
| Read model | `operator_flow_read_model` |
| API | GET `/operator`; POST `/api/v1/operator/actions/*` |
| Actions | QD accept/reject, deal/CO human actions |
| Authority | `_trusted_cockpit_operator` / human |
| Sufficiency | **LIVE** for intake/outcome; naming is engineering-heavy |

### Legacy Cockpit (`/cockpit`)

| Field | Contract |
|-------|----------|
| Read model | `cockpit_read_model` |
| Sufficiency | **DUPLICATE attention** vs Home — fold, don’t extend |

### Sales (`/sales`)

| Field | Contract |
|-------|----------|
| Source | sales templates + prospecting APIs |
| Sufficiency | **THIN** vs Contact workspace |

### Marketing surfaces

| Screen | Backend | Sufficiency |
|--------|---------|-------------|
| Studio / editorial / publishing / SEO | Existing Marketing APIs + FS SoT | **LIVE engines**, not commercial graph |
| `/marketing` | marketing landing | THIN |

### Analytics (`/analytics`)

In-memory / mixed metrics. **INSUFFICIENT** as Revenue OS product. Not COS-1 blocker if Home doesn’t fake ARR.

### Login

Identity cookie. Sufficiency **LIVE**.

---

## Canonical mutation APIs (Founder commercial loop)

| Action | Endpoint family | Revalidation |
|--------|-----------------|--------------|
| Research → draft | `/api/v1/revenue/contacts/{id}/research-to-outreach` | tenant + human |
| Follow-up propose | `.../follow-up/propose` | M2.5 stale authority |
| Booking eligibility | `.../booking/eligibility` | M4 |
| Availability | `.../booking/availability` | connector + tenant |
| Propose booking | `.../booking/propose` | eligibility + slot |
| Approve | `/api/v1/approvals/{id}/approve` | execution-time M4.5 |
| QD / CO | operator + MC04/MC06 services | human + idempotency |

---

## Screens with insufficient backend for conceptual IA

| Desired screen | Gap |
|----------------|-----|
| Account workspace | no Company read model / route |
| Opportunity workspace | no Deal UI contract |
| Revenue overview / forecast | no tenant-safe forecast API as Founder screen |
| ICP / positioning settings | no attested context SoT |
| AI Work inbox | scattered across Home + Approvals |
| Audience | no entity |
| Campaign performance | engine-specific, not graph |
| Global search | service exists; not wired to Founder shell |

These are **roadmap**, not excuses to stub data in templates.
