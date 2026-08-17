# CP1 — Marketing OS Readiness (HERMES)

**Sprint:** CP1  
**Evidence:** `docs/marketing/social/S0_R_*`, S0 decision pack  
**Revalidation:** Do not assume stale blockers without S0-R

---

## Social S1 proposed scope (unchanged)

LinkedIn-only manual publisher: human-approved text (+ optional link); one identity; no media/schedule/analytics/autonomous publish; fakes in tests; live API after ES.

---

## What prevents Social S1 TODAY?

| Blocker | Class | Prevents what? |
|---------|-------|----------------|
| FD-01 identity not ratified | **FOUNDER_DECISION** | Live identity choice; soft for member-default design |
| ES-01 Developer app | **EXTERNAL** | Live LinkedIn calls |
| ES-02 Product + OAuth | **EXTERNAL** | Live LinkedIn calls |
| ES-03 Token in env/vault | **EXTERNAL** | Live LinkedIn calls |
| ES-04 org admin | **EXTERNAL** (conditional) | Org identity only |
| IB-01 LinkedIn adapter | **ENGINEERING** | **Is S1 work** — not a pre-start hard stop |
| IB-02 Social package | **ENGINEERING** | **Is S1 work** |
| IB-03 OAuth bind | **ENGINEERING** | CONDITIONAL — env token path allowed |
| Architecture / Editorial / Publishing gates | **NONE** | PASS — ready to consume |
| Frozen Marketing contract change needed | **NONE** | UNCHANGED |

**No actual architecture hard blocker** to starting S1 **behind fakes**.

**Live publish** blocked by **EXTERNAL** (+ **FOUNDER_DECISION** for identity).

**Marketing Social S1 Readiness:** **CONDITIONAL** — engineering start OK; live publish NOT READY.

---

## Verdict for CP1

Social S1 remains **CONDITIONAL GO** per S0-R. Selecting it as next sprint requires Founder acceptance of FD-01 path (or CONFIGURABLE default) and acceptance that live LinkedIn waits on ES-01..03.
