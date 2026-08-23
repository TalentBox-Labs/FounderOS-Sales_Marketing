# F0 — Founder Decision Record

Sprint F0 — Founder fillable form  
Date opened: 2026-08-09  
**Status: RATIFIED** (Sprint E7 brief, 2026-08-09)

Review packet: [F0_FOUNDER_DECISION_REVIEW.md](F0_FOUNDER_DECISION_REVIEW.md)  
Related: [E6D_IMPLEMENTATION_DECISION_MATRIX.md](E6D_IMPLEMENTATION_DECISION_MATRIX.md), [ADR_EDITORIAL_APPROVAL_SEMANTICS.md](../architecture/adr/ADR_EDITORIAL_APPROVAL_SEMANTICS.md), [E7_IMPLEMENTATION_REPORT.md](../editorial/E7_IMPLEMENTATION_REPORT.md)

---

## FDR-001 (E6C FD-1) — Approval object

**Question:** For Sprint E7 Editorial Approval, what is the approved object: a phase-scoped staged artifact bundle (2A / 2B / 3), a single content-item approval spanning the week, or both?

**Available Options:**

- **A** — Phase-scoped promote only  
- **B** — Content-item approval only  
- **C** — Both phase promote and content-item overlay  

### Founder Decision

| Field | Value |
|-------|-------|
| Decision ID | FDR-001 |
| Selected Option | **A** |
| Founder Policy | Phase-scoped promote only |
| Constraints | Approve invokes `promote_staged` for one phase (2a / 2b / 3) |
| Deferred Items Accepted | FD-3, FD-4, FD-7, FD-8 |
| Approved | **YES** |
| Date | 2026-08-09 |
| Notes | Ratified in Sprint E7 mission brief |

---

## FDR-002 (E6C FD-2) — Approver identity

**Question:** Who may act as Editorial Approver for E7, and how is AI / automation prevented from serving as approver: ops free-text name, Shared Platform authenticated user + role, or free-text plus explicit deny of automation keys?

**Available Options:**

- **A** — Free-text human name (ops trust)  
- **B** — Shared Platform authenticated user + role  
- **C** — Free-text + deny automation keys for approve  

**Invalid (not selectable as approver):** AI agent / QACrew / system automation as Editorial Approver (ADR).

### Founder Decision

| Field | Value |
|-------|-------|
| Decision ID | FDR-002 |
| Selected Option | **A** (+ deny-list for AI/automation names) |
| Founder Policy | Human approval only; AI may recommend but never approve |
| Constraints | AI/automation is NOT an Editorial Approver: **YES** |
| Deferred Items Accepted | FD-8 (platform role ACL) |
| Approved | **YES** |
| Date | 2026-08-09 |
| Notes | E7 blocks known automation identity tokens (ai, bot, crewai, …) |

---

## FDR-003 (E6C FD-5) — Publishing boundary

**Question:** Does a successful Editorial Approval (promote attestation) authorize Publishing Engine execution, or is it editorial-only (publish/go-live remain separate)?

**Available Options:**

- **A** — Editorial-only (never authorizes publish)  
- **B** — Necessary but not sufficient for publish (E7 still must not auto-publish)  
- **C** — Approval alone may trigger publish automation  

**Not permitted as publish auth:** Readiness summary or tracker `QA Passed` alone (ADR / E6B.5).

### Founder Decision

| Field | Value |
|-------|-------|
| Decision ID | FDR-003 |
| Selected Option | **A** |
| Founder Policy | Editorial approval does NOT authorize publishing |
| Constraints | No go-live / Hashnode / publish side effects from approval path |
| Deferred Items Accepted | Publishing Engine precondition wiring; FD-8; Calendar |
| Approved | **YES** |
| Date | 2026-08-09 |
| Notes | Ratified in Sprint E7 mission brief |

---

## Packet completion

| Check | Status |
|-------|--------|
| FDR-001 Approved = YES | **YES** |
| FDR-002 Approved = YES | **YES** |
| FDR-003 Approved = YES | **YES** |
| ADR may be amended PROPOSED → Accepted | **DONE** |
| Sprint E7 unblocked | **YES** |

**Founder sign-off**

| Field | Value |
|-------|-------|
| Name | (ratified via Sprint E7 mission brief) |
| Date | 2026-08-09 |
| Signature / ack | RATIFIED |
