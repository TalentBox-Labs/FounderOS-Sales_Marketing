# Founder OS Controlled Parallelism Model v1

**STATUS:** GOVERNANCE  
**Sprint:** COS-ARCH-v1  
**Baseline:** `a7463e5`

---

## Streams

### STREAM A — Commercial backend architecture

Canonical graph, services, event overlay, authority, APIs, read models.  
Owns: entity SoT decisions, facades, tenant keys on commercial rows, scorer/API dual-stack **plans** (not silent merges).

### STREAM B — Founder OS experience

IA, terminology, design-system **requirements**, screens, usability.  
Owns: templates **only after** Stream A contracts exist for any new field. COS-ARCH-v1 is B+A docs; no template edits.

### STREAM C — Integrated commercial slice

End-to-end Marketing → Sales → Revenue → Founder **using existing spine** (COS-1).  
Owns: wiring, demo journey, certification. Must not invent SoT.

---

## Shared locks (no stream may redefine alone)

- Canonical entities and aliases (Lead/Opportunity/Account)
- Authority semantics (HUMAN_ONLY, approval, proposal-only)
- Tenant semantics (`Organization`, `TenantContext`)
- Lifecycle enums (`ContactStatus`, `DealStage`, approval status, booking ui_state)
- Shared event overlay names vs runtime `action_type`

---

## Change protocol

1. **Propose** in a doc ADR under `docs/founder_os/` or architecture ADR.  
2. **Classify** SoT vs derived vs UI copy.  
3. **Map** frozen baselines affected (Sales A1.5, M4.5, UI-D1.5, UI-D2, S1–S4).  
4. **If freeze conflict:** explicit unfreeze sprint — do not “fix” frozen tests to match new UI absence/presence.  
5. **Stream B** consumes Stream A field names; no Jinja-only lifecycles.  
6. **Stream C** cannot ship a step whose SoT is Stream A-unknown.  
7. **Demo seeds** (`seed_founder_demo.py`) cannot become production architecture (DEMO-D1.x is compatibility, not graph law).  
8. Cross-stream review: authority + tenant owners sign before merge.

---

## Anti-patterns

- Stream B adding `requested_by` to POST bodies to “make the API work”
- Stream A adding `leads` table because the UI said Leads
- Stream C using `demo.db` contamination as product state
- Parallel Command + Cockpit features

---

## RACI (summary)

| Decision | A | B | C |
|----------|---|---|---|
| New entity | R | C | I |
| Copy/terminology | C | R | I |
| Journey certification | C | C | R |
| Authority matrix | R | I | C |
| Tenant isolation | R | I | C |
