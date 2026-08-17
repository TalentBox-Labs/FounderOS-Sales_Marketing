# E6D — Implementation Decision Matrix

Sprint E6D — Governance only  
Date: 2026-08-09  
Code changes: **0**  
Architecture: **UNCHANGED**

Sources: [ADR_EDITORIAL_APPROVAL_SEMANTICS.md](../architecture/adr/ADR_EDITORIAL_APPROVAL_SEMANTICS.md), [E6C_FOUNDER_DECISIONS.md](../migration/editorial-engine/E6C_FOUNDER_DECISIONS.md), [E6B_5_READINESS_BASELINE_FREEZE.md](../migration/editorial-engine/E6B_5_READINESS_BASELINE_FREEZE.md), [09_APPROVAL_BOUNDARY.md](../migration/editorial-engine/09_APPROVAL_BOUNDARY.md), [15_SPRINT_E6A_VERDICT.md](../migration/editorial-engine/15_SPRINT_E6A_VERDICT.md)

**This sprint does not answer Founder decisions.** It prioritizes them for implementation sequencing.

---

# Executive Summary

Eight unresolved Founder decisions (FD-1…FD-8) remain from E6C.

| Bucket | Count | IDs |
|--------|------:|-----|
| **BLOCKER** | 2 | FD-1, FD-2 |
| **IMPLEMENTATION** | 1 | FD-5 |
| **RELEASE** | 1 | FD-8 |
| **FUTURE** | 4 | FD-3, FD-4, FD-6, FD-7 |

**Minimum Founder decisions before Sprint E7: 3** — FD-1, FD-2, FD-5.

E7 (recommended) is a thin **Approval Command** over existing `promote_staged` + `promotion_audit`, under the ADR interim model (phase-scoped, human-attested, editorial-only). That path does **not** require lifecycle states, rejection UX, revocation, or readiness coupling.

Interim CLI promote may continue operationally; E7 productization cannot be designed until the three minimum decisions are made.

---

# Decision Inventory

| ID | Question | Repository evidence | Current assumption (if any) | Impact | Owner |
|----|----------|---------------------|-----------------------------|--------|-------|
| **FD-1** | Phase-scoped promote only vs content-item approval overlay? | `promote_staged` copies phase file sets; no content-row approval entity; ADR interim = phase bundle | ADR interim: phase-scoped only | Shapes E7 API object, persistence, Lifecycle need | Founder + Editorial Engine |
| **FD-2** | Free-text approver vs authenticated role; AI enforcement? | `--approver` / `WORKCREW_PROMOTION_APPROVER`; no ACL; ADR: AI approval NOT ALLOWED (intent) | ADR: human free-text ALLOWED today; AI NOT ALLOWED | Auth, Shared Platform, API security | Founder + Shared Platform + Editorial |
| **FD-3** | Must readiness / tracker QA be promote prerequisites? | Promote uses `validate_staged` only; readiness API not consulted | Optional (ADR) | Couples Readiness/pipeline to approve | Founder + Editorial Engine |
| **FD-4** | Tracker/lifecycle “Approved” state vs audit+FS only? | Promote does not mutate tracker status; CMS stages reference-only | ADR interim: no new lifecycle state | Content Studio/Kanban contract; Lifecycle ADR if yes | Founder + Editorial + Lifecycle ADR |
| **FD-5** | Does Editorial Approval authorize Publishing Engine? | Promote ≠ publish; go-live/hashnode separate; checklist human note | ADR Decision A: editorial-only | Publishing Engine boundary; automation risk | Founder + Editorial + Publishing |
| **FD-6** | Formal rejection semantics? | No content-promote reject; Revenue OS reject unrelated | None — validation FAIL only blocks promote | Reject API/CLI; possible lifecycle | Founder + Editorial |
| **FD-7** | Revoke / invalidate after post-promote edit? | Backups exist; no revoke API; re-promote can overwrite | Implicit supersession via new promote | Watchers, audit chain | Founder + Editorial |
| **FD-8** | Extra audit fields (user id, correlation, previous decision)? | `promotion_audit` has approver, UTC, week, paths, validators, git SHA, notes, backup | Current audit sufficient for CLI | Prod audit/compliance depth | Founder + Editorial + Shared Platform |

---

# Decision Classification

Exact one bucket each:

| ID | Bucket |
|----|--------|
| FD-1 | **BLOCKER** |
| FD-2 | **BLOCKER** |
| FD-5 | **IMPLEMENTATION** |
| FD-8 | **RELEASE** |
| FD-3 | **FUTURE** |
| FD-4 | **FUTURE** |
| FD-6 | **FUTURE** |
| FD-7 | **FUTURE** |

---

# Blockers

## FD-1 — Approval object granularity

| Aspect | Detail |
|--------|--------|
| **Why it blocks** | E7 Approval Command cannot define request/response or persistence until the object is known (phase bundle vs content-item record). Choosing B/C forces Lifecycle ADR + new SoT before coding. |
| **Affected modules** | Future approval router/service; `promote_staged` (caller contract); Content Studio if content-item overlay |
| **Affected APIs** | Any `POST` approval/promote surface; readiness remains GET-only |
| **Affected runtime** | Staging → `input/` copy path; no Celery today |
| **Affected tests** | New approval tests; promote/audit fixtures |
| **Rollback impact** | If wrong object shipped: revert API + any new records; FS promotes may already have occurred (ops) |

## FD-2 — Approver identity & AI enforcement

| Aspect | Detail |
|--------|--------|
| **Why it blocks** | E7 HTTP/API design differs completely for free-text (status quo) vs Shared Platform auth roles. AI-as-approver prevention must be explicit before exposing promote beyond CLI trust boundary. |
| **Affected modules** | Approval command; `_verify_api_key` / future auth; `promote_staged` approver plumbing |
| **Affected APIs** | Auth headers, actor fields, deny automation keys |
| **Affected runtime** | Who may invoke promote from API workers |
| **Affected tests** | Auth/negative tests; no-AI-approver guarantees |
| **Rollback impact** | Revert auth wiring; CLI free-text path can remain |

**Why two blockers (not zero):** ADR interim semantics allow ops CLI continue, but **Sprint E7 product implementation** cannot begin design without object + authority. These are not optional product preferences; they are interface contracts.

---

# Implementation Decisions

## FD-5 — Publishing authorization coupling

| Aspect | Detail |
|--------|--------|
| **Earliest sprint** | **E7** (before any Approval Command that could be misread as publish) |
| **Can default safely?** | ADR already states Decision A (editorial-only). Safe **technical** default exists; still needs Founder **affirmation** so Publishing Engine is not wired. |
| **Must Founder decide?** | **Yes** — confirm A, or explicitly choose B/C (B/C expands scope beyond E7). |
| **Can ADR postpone?** | Not for E7 if E7 exposes approve/promote. Can postpone only if E7 deferred entirely. |

---

# Release Decisions

## FD-8 — Audit field expansion

| Aspect | Detail |
|--------|--------|
| **Risk if deferred** | Weaker correlation/compliance trail in production; CLI audit still exists |
| **Operational impact** | Harder to trace who approved across systems |
| **Security impact** | Free-text approver remains spoofable without auth user id (ties to FD-2) |
| **Compliance impact** | May be insufficient if formal audit/compliance required for content promotion |

Ship E7 to non-prod / trusted ops with current `promotion_audit` fields if FD-2 Option A; strengthen FD-8 before broad production.

---

# Future Decisions

| ID | Reason deferrable | Potential future sprint |
|----|-------------------|-------------------------|
| **FD-3** | Promote already gates via `validate_staged`; readiness is frozen read model and need not be mandatory for E7 | E7.x / E8 preconditions tightening |
| **FD-4** | ADR interim = no new tracker state; Content Studio/Kanban frozen on existing `status` strings; Option B needs Lifecycle ADR first | Post–Lifecycle ADR |
| **FD-6** | No reject path today; E7 can be approve/promote-only (validation failure already blocks) | E8 Rejection |
| **FD-7** | Re-promote + backups provide operational supersession; formal revoke not required for first command | E8+ Revocation |

---

# Dependency Graph

Repository-evidence chain (not aspirational invention):

```
Editorial Readiness (E6B FROZEN — GET evidence only)
        ↓
Approval Command (E7 candidate — wrap/attest promote_staged)
        ↓
Audit (promotion_audit — already exists; FD-8 may enrich)
        ↓
Publishing Authorization (SEPARATE — FD-5; not granted by Editorial Approval)
        ↓
Publishing Engine (go_live_helpers / hashnode_publish — existing, human confirm)
        ↓
Campaign Engine (NOT VERIFIED as dependent on Editorial Approval in Founder path)
        ↓
Automation (Celery/OpenClaw — not on content promote path today)
```

Evidence notes:

- Readiness does not approve ([editorial.py](../../runner_api_routers/editorial.py), E6B.5 freeze).
- Approval Command target = existing promote + audit (E6C ADR).
- Publishing is explicitly decoupled unless Founder chooses FD-5 B/C.
- Campaign Engine / Automation are **not** evidenced as next hard dependencies of Editorial Approval; shown as later platform layers only.

---

# Recommended Founder Decisions

**Ask the Founder to decide these three before Sprint E7:**

| Priority | ID | Decision needed (options from E6C — not selected here) |
|----------|----|--------------------------------------------------------|
| 1 | **FD-1** | Confirm E7 object = phase-scoped promote only (A), or expand to content-item (B/C) |
| 2 | **FD-2** | Confirm E7 identity = free-text human name (A), Shared Platform auth (B), or A+automation deny (C) |
| 3 | **FD-5** | Confirm Editorial Approval never authorizes publish (A), or choose B/C with Publishing scope |

**Explicitly not required before E7:** FD-3, FD-4, FD-6, FD-7, FD-8 (FD-8 before production release).

---

# Next Sprint Recommendation

| Sprint | Recommendation |
|--------|----------------|
| **Now** | Founder Decision Review on FD-1, FD-2, FD-5 |
| **E7** (after those three) | Approval Command — thin, evidence-aligned surface over `promote_staged` + existing audit; no lifecycle invent; no publish; no reject/revoke unless Founder expands scope |
| **Later** | FD-8 for production hardening; FD-6/FD-7 for reject/revoke; FD-4 only with Lifecycle ADR; FD-3 if coupling readiness is desired |

Amend [ADR_EDITORIAL_APPROVAL_SEMANTICS.md](../architecture/adr/ADR_EDITORIAL_APPROVAL_SEMANTICS.md) from **PROPOSED** → **Accepted** only after the three minimum decisions are recorded.

---

# Counts

| Metric | Value |
|--------|------:|
| Founder Decisions total | 8 |
| Implementation Blockers | 2 |
| Implementation Decisions | 1 |
| Release Decisions | 1 |
| Future Decisions | 4 |
| Minimum before E7 | 3 |
| Code changes this sprint | 0 |
