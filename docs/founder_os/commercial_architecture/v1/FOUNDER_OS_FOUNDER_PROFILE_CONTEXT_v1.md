# Founder OS Founder Profile & Company Context v1

**STATUS:** ARCHITECTURE ONLY  
**Sprint:** COS-ARCH-v1  
**Baseline:** `a7463e5`

Founder Profile is **operating context**, not a social profile page and not a CRM `Company` row for prospects.

---

## 1. Layer separation (mandatory)

| Layer | Meaning | May AI write? | Repository today |
|-------|---------|---------------|------------------|
| **A. Authoritative company truth** | Mission, product, market, model, stage — founder-attested | **Never silently** | **Missing.** Do not use prospect `Company` |
| **B. Founder/user preferences** | Style, working hours, UI density | Suggest only | `User.preferences` Text (unstructured) |
| **C. Goals** | ARR, pipeline, customers, initiatives | Track progress; not invent targets | Hermes `Goal` is **planner metrics**, wrong layer |
| **D. Authority preferences** | What AI may do | No — human settings | Contracts exist; **no settings SoT/UI** |
| **E. AI inference** | Guessed ICP, inferred tone | Yes, labeled inference | Copilot / research workers — not persisted as truth |
| **F. Derived intelligence** | What changed, risk, next action | Yes, labeled derived | Command / cockpit / contact read models |

**Law:** E and F must never be stored as A.

---

## 2. Identity vs workspace vs CRM

| Object | Role |
|--------|------|
| `User` | Who is signed in |
| `Organization` | Tenant / workspace |
| `OrganizationMembership` | Role in workspace |
| CRM `Company` | External account |
| **FounderWorkspaceContext (proposed)** | A–D for this Organization |

Do not model the founder’s company as a Contact.

---

## 3. Proposed context groups (not implemented)

### Founder (B)

- identity (from User)
- role (membership + User.role — dual role fields = debt)
- communication style, working preferences
- approval preferences / risk tolerance → feeds D

### Company (A)

- mission, product, market, business model, stage, geography, competitors  
Storage: Organization-scoped document, versioned, `attested_by` user id, `attested_at`.

### Commercial strategy (A, founder-attested)

- ICP, personas, positioning, value propositions, pricing, sales motion, marketing motion  
Marketing engines may *use* this; they do not *own* it.

### Goals (C)

- ARR, pipeline, customers, growth priorities, current initiatives  
Separate table from `hermes_goals`. Hermes may *read* C to plan; C is not a Hermes row.

### Authority (D)

Align to existing matrices (Sales agent + Rev-orch M0.5–M4.5):

| Capability | Default (current frozen behavior) |
|------------|-----------------------------------|
| AI can research | yes |
| AI can score | yes (status promotion restricted) |
| AI can draft | yes |
| AI can recommend | yes, advisory |
| AI can follow up / send / book | **no** — approval |
| Explicitly prohibited | credential changes, cross-tenant, calendar without approve, Contact/Deal mutation from UI inference |

Settings UI later must **narrow** autonomy, never silently widen beyond frozen tests.

---

## 4. Tenant

All A–D rows: `organization_id` required. No global founder profile across orgs.

---

## 5. UI

- Company section in hierarchy (settings)
- Home may show **attested** ICP one-liner + **derived** “what matters”
- Inference badges: “Suggested by AI — not saved as company truth”

---

## 6. COS-1 scope

Stub: read-only display of Organization name + User + existing operator flag.  
Do **not** implement a new profile schema in COS-ARCH-v1 (this sprint is docs only). COS-1 foundation may add a **minimal attested context document** behind an ADR, not a parallel CRM.
