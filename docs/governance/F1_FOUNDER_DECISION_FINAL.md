# F1 — Founder Decision Finalization

Sprint F1 — Governance only  
Date: 2026-08-09  
Code / API / DB / YAML / Git changes: **0**  
Architecture: **UNCHANGED**

Sources: [F0_FOUNDER_DECISION_REVIEW.md](F0_FOUNDER_DECISION_REVIEW.md), [F0_FOUNDER_DECISION_RECORD.md](F0_FOUNDER_DECISION_RECORD.md), [ADR_EDITORIAL_APPROVAL_SEMANTICS.md](../architecture/adr/ADR_EDITORIAL_APPROVAL_SEMANTICS.md), [E6D_IMPLEMENTATION_DECISION_MATRIX.md](E6D_IMPLEMENTATION_DECISION_MATRIX.md)

---

# Executive Summary

| Item | Count / status |
|------|----------------|
| Remaining unresolved in F0 record | **3** (FDR-001, FDR-002, FDR-003) |
| Resolved by F1 recommended package | **3** (pending Founder ratification below) |
| Deferred safely (not E7 blockers) | FD-3, FD-4, FD-6, FD-7, FD-8 |
| Implementation blockers after ratification | **0** |
| E7 can begin | **CONDITIONAL GO** — proceed under recommended options once Founder ratifies this document |

Recommendations follow **repository evidence** and the Editorial Approval ADR interim model (phase-scoped promote, human approver, editorial ≠ publish). They do not invent lifecycle or CMS Sheets semantics.

---

# Remaining Decisions

All three F0 slots are still blank (`Selected Option` unset; `Approved` ≠ YES).

| Decision ID | E6C ID | Problem (one-line) | Blocking |
|-------------|--------|--------------------|----------|
| FDR-001 | FD-1 | What object does E7 approve? | BLOCKER |
| FDR-002 | FD-2 | Who may approve; how is AI blocked? | BLOCKER |
| FDR-003 | FD-5 | Does approval authorize publish? | IMPLEMENTATION (E7 gate) |

---

# Recommended Decisions

## FDR-001 — Approval object

| Field | Content |
|-------|---------|
| **Decision ID** | FDR-001 |
| **Problem** | E7 must know whether approval is phase-scoped promote, content-item approval, or both |
| **Options** | **A** Phase-scoped promote only · **B** Content-item only · **C** Both |
| **Recommended option** | **A — Phase-scoped promote only** |
| **Trade-offs** | A matches CLI today, lowest blast; B/C need new SoT + likely Lifecycle ADR before E7 |
| **Repository impact** | Reuse `promote_staged` phase file sets; no tracker enum; no new DB |
| **Implementation impact** | API: `content_id`/`week_id` + `phase` + approver; call existing promote/audit |
| **Backward compatibility** | Full — CLI promote unchanged |
| **Risk** | LOW — product cannot express “whole week approved” without later overlay |
| **Rollback** | Remove E7 routes; CLI remains |
| **Affected modules** | Editorial Engine; `promote_staged`; `promotion_audit`; optional `editorial` router |
| **Blocking status** | BLOCKER until decided — **recommended A clears blocker** |

---

## FDR-002 — Approver identity

| Field | Content |
|-------|---------|
| **Decision ID** | FDR-002 |
| **Problem** | E7 must define who may act as Editorial Approver and bar AI/automation |
| **Options** | **A** Free-text human name · **B** Shared Platform auth + role · **C** Free-text + deny automation keys |
| **Recommended option** | **A — Free-text human name (ops trust)** + mandatory affirmation: **AI/automation is NOT an Editorial Approver** |
| **Trade-offs** | A matches `promote_staged` / `WORKCREW_PROMOTION_APPROVER` today; spoofable if HTTP is exposed broadly. B strongest but may block E7 if role auth incomplete. C middle ground — **allowed hardening in E7** if approve is HTTP-public; not required for CLI-parity E7 |
| **Repository impact** | Pass `approver` string into promote/audit; no Revenue OS approvals reuse |
| **Implementation impact** | Request body/header `approver`; reject empty; document AI ban in API docs/tests |
| **Backward compatibility** | Full with CLI |
| **Risk** | MEDIUM if HTTP approve is internet-reachable without extra controls — mitigate with API key + ops trust or adopt C in same sprint |
| **Rollback** | Revert endpoint; CLI env approver remains |
| **Affected modules** | Editorial Engine; Shared Platform API key (existing); not Revenue JWT unless B chosen later |
| **Blocking status** | BLOCKER until decided — **recommended A + AI ban clears blocker** |

**Invalid (unchanged):** AI agent / QACrew / system automation as Editorial Approver.

---

## FDR-003 — Publishing boundary

| Field | Content |
|-------|---------|
| **Decision ID** | FDR-003 |
| **Problem** | Must E7 approval trigger or authorize Publishing Engine? |
| **Options** | **A** Editorial-only · **B** Necessary but not sufficient for publish · **C** Approval may trigger publish |
| **Recommended option** | **A — Editorial-only (never authorizes publish)** |
| **Trade-offs** | A matches ADR interim + current promote≠publish evidence. B allows later Publishing checks without E7 auto-publish. C couples engines and breaks frozen separation |
| **Repository impact** | No calls to `go_live_helpers` / `hashnode_publish` from approve path |
| **Implementation impact** | E7 ends at promote + audit; tests forbid publish side effects |
| **Backward compatibility** | Full — publish paths unchanged |
| **Risk** | LOW — operators must still run publish/go-live separately (already true) |
| **Rollback** | N/A for publish (nothing wired) |
| **Affected modules** | Editorial Engine only in E7; Publishing Engine untouched |
| **Blocking status** | E7 gate — **recommended A clears gate** |

**Not permitted:** Readiness summary or tracker `QA Passed` as publish authorization.

---

# Implementation Order

1. **Founder ratifies** Decision Table (this document) — or overrides in writing.  
2. Amend [ADR_EDITORIAL_APPROVAL_SEMANTICS.md](../architecture/adr/ADR_EDITORIAL_APPROVAL_SEMANTICS.md) **PROPOSED → Accepted** with FDR-001=A, FDR-002=A (+ AI ban), FDR-003=A.  
3. Update [F0_FOUNDER_DECISION_RECORD.md](F0_FOUNDER_DECISION_RECORD.md) Selected Option / Approved = YES.  
4. Start **Sprint E7 — Editorial Approval Command** per [08_NEXT_SPRINT_RECOMMENDATION.md](08_NEXT_SPRINT_RECOMMENDATION.md).  
5. Parallel (optional): T1 Ruff tooling (Toolchain v1.0).

---

# Risk Matrix

| ID | Rec | Risk if adopted | Risk if delayed |
|----|-----|-----------------|-----------------|
| FDR-001 A | LOW | Weak “week approved” product story | E7 blocked / wrong object built |
| FDR-002 A | MEDIUM (HTTP spoof) | Ops trust required | E7 blocked; or B delays on auth |
| FDR-003 A | LOW | Manual publish remains | Accidental publish coupling |

| Deferred | Risk if pulled into E7 |
|----------|------------------------|
| FD-3 readiness mandatory | Couples read model to mutate path |
| FD-4 lifecycle Approved status | Lifecycle ADR + CS/Kanban contract break |
| FD-6/FD-7 reject/revoke | Scope explosion |
| FD-8 audit enrichment | Release hardening, not E7 |

---

# Decision Table

| Decision ID | Question (short) | Recommended | Affirmations | Deferred accepted |
|-------------|------------------|---------------|--------------|-------------------|
| FDR-001 | Approval object | **A** Phase-scoped promote only | — | FD-3, FD-4, FD-6, FD-7, FD-8 |
| FDR-002 | Approver identity | **A** Free-text human name | **AI/automation NOT approver = YES** | FD-8; Option B later; Option C optional harden |
| FDR-003 | Publish boundary | **A** Editorial-only | Readiness/QA Passed ≠ publish auth | Publishing precondition wiring; Calendar |

---

# Final Go / No-Go

| Check | Status |
|-------|--------|
| Recommendations evidence-aligned | YES |
| Architecture change required | NO |
| DB change required | NO |
| Code in F1 | NO |
| Founder ratification of this table | **REQUIRED** |

### Verdict

**CONDITIONAL GO for E7**

- **GO** to implement E7 against recommended **A / A / A** immediately after Founder ratification of this document (or written override).  
- **NO-GO** to merge E7 without ratification or without ADR Accepted update.  
- Implementation blockers remaining **after ratification: 0**.

---

## Founder ratification (sign here)

| Field | Value |
|-------|-------|
| Adopt F1 recommended Decision Table (A / A / A)? | YES / NO / OVERRIDE (attach) |
| AI/automation is NOT an Editorial Approver | YES / NO |
| Name | |
| Date | |
| Signature / ack | |

Once YES: copy selections into [F0_FOUNDER_DECISION_RECORD.md](F0_FOUNDER_DECISION_RECORD.md) and proceed to E7.
