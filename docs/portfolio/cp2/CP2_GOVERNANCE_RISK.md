# CP2 — Governance & Security Risk (SENTINEL)

**Sprint:** CP2  
**Date:** 2026-08-13  
**Pattern:** MACHINE MAY ANALYZE / RECOMMEND → HUMAN AUTHORIZES MATERIAL MUTATION → CANONICAL SoT MUTATES → AUDIT RECORDS

---

## Candidate risk matrix

| Candidate | Human authority | Agent risk | Credential/OAuth | Cross-OS mutation | Audit | Verdict |
|-----------|----------------|------------|----------------|-------------------|-------|---------|
| **A** Companies runner | API key; no stage/status gate needed for CRUD | Low — read-heavy CRM | None | Low — Revenue Company SoT only | Standard API | **COMPATIBLE** |
| **B1** Social S1 live | Editorial + publish gates PASS | Medium — OAuth token storage | **HIGH** — ES-01..03, FD-01 | Low if boundary preserved | Publishing audit pattern | **CONDITIONAL** |
| **B2** Social S1 fake | Same gates | Low in fake mode | None in CI | Low | Testable | **COMPATIBLE** |
| **C** QualifiedDemand | HUMAN_ONLY intake acceptance per contract | **Medium** — must block agent auto-create | None v1 | **Medium** — boundary-critical; no shared SoT | Required: accept/reject audit | **COMPATIBLE** if scoped |
| **D1** SEO incremental | Read-only audit engines | Low | None | None | Engine reports | **COMPATIBLE** |
| **D2** SEO production | Indexing safety gates | Medium if mis-activated | GSC credentials | None | Indexing attestation | **BLOCKED** until domain |
| **E** CommercialOutcome | Human close already gated (A3.5) | Low if stub only | None v1 | Medium — Sales→Revenue event | Event + audit required | **COMPATIBLE** |

---

## QualifiedDemand governance checklist

| Rule | Status |
|------|--------|
| Marketing cannot write Revenue CRM directly | Enforceable — contract frozen |
| Sales cannot mutate Marketing qualification state | Enforceable |
| No shared SoT | Enforceable — event handoff only |
| Agent auto-create prohibited | Must gate intake acceptance |
| PII/consent in payload | Contract fields defined |

**Preferred for Founder OS governance maturity:** Candidate C aligns with established A3/A4 human-gate pattern at Sales acceptance boundary.
