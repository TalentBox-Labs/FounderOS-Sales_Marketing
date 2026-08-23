# 05 — Development Rulebook

Sprint P0 — Documentation only  
Date: 2026-08-09

---

## Core rules

1. **Never bypass ADRs** — Editorial Approval, Calendar semantics, and future ADRs bind implementation.  
2. **Never change frozen APIs** without an explicit unfreeze + contract version note (Content Studio JSON, Readiness shape).  
3. **Never duplicate business logic** — reuse builders (`build_content_*`, `build_editorial_readiness`, validators).  
4. **Never migrate without evidence** — CMS is REFERENCE ONLY; Founder remains canonical.  
5. **No architecture redesign** — Architecture Baseline frozen; additive only.  
6. **One feature per sprint** — single objective; no drive-by refactors.  
7. **Evidence first** — repository paths, tests, runtime proof before claims.  
8. **Regression mandatory** — focused tests + relevant suite; record counts.  
9. **Read-only means read-only** — no silent writes from “view” surfaces.  
10. **Toolchain gates** — Toolchain Baseline v1.0; paid tools need Founder approval.  
11. **Approval domains stay split** — Revenue OS approvals ≠ Editorial promote.  
12. **No inventing lifecycle/status** — tracker strings and readiness summaries are observational unless Lifecycle ADR says otherwise.  
13. **Sales OS Architecture Baseline v1.0 FROZEN** — After SALES A1.5 / ADR-005, do not silently change Sales domain model, Marketing↔Sales ownership, Sales↔Revenue ownership, Sales agent authority, Sales integration disposition, or CRM UI disposition (`RETAIN_AND_REFACTOR_LATER`). Implement against contracts; amend only via explicit ADR + approved sprint. See `docs/sales/SALES_A1_5_BASELINE_MANIFEST.md`.  
14. **Sales Runner Deal Stage Update Baseline v1.0 FROZEN** — After SALES A3.5 / ADR-007, do not silently change human-gated runner deal stage behavior, agent prohibition, audit expectation, or closed_won / CommercialOutcome boundary. See `docs/sales/SALES_A3_5_BASELINE_MANIFEST.md`.

---

## Definition of Ready

A sprint may start only if:

- [ ] Objective fits one module owner  
- [ ] Dependencies identified (hard/soft)  
- [ ] Blocking Founder/ADR decisions resolved or explicitly out of scope  
- [ ] Frozen baselines listed that must not break  
- [ ] Test plan sketched (focused + regression scope)  
- [ ] Rollback path named  
- [ ] No paid tool introduction without Founder approval  

---

## Definition of Done

A sprint is done only if:

- [ ] Objective met with repository evidence  
- [ ] Focused tests pass (new or existing)  
- [ ] Agreed regression scope run; counts recorded  
- [ ] No new regressions vs declared baseline (or justified)  
- [ ] Frozen contracts unchanged (or versioned unfreeze documented)  
- [ ] Docs updated if governance/API surface changed  
- [ ] Rollback path still valid  
- [ ] No unauthorized paid tooling  
- [ ] Architecture impact stated (default: UNCHANGED)  

---

## Sprint hygiene

| Practice | Rule |
|----------|------|
| Commits | Only when user requests; no secrets |
| Scope creep | Stop; open follow-up sprint |
| STOP conditions | Honor sprint STOP (ADR required, etc.) |
| Parallel work | Follow [04_PARALLEL_DEVELOPMENT_GUIDE.md](04_PARALLEL_DEVELOPMENT_GUIDE.md) |
