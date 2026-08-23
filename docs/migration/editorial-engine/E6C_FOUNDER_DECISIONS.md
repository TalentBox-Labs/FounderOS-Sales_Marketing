# E6C — Founder Decisions Required (Editorial Approval)

Sprint E6C — Governance only  
Date: 2026-08-09  
ADR: [ADR_EDITORIAL_APPROVAL_SEMANTICS.md](../../architecture/adr/ADR_EDITORIAL_APPROVAL_SEMANTICS.md)

**Do not select defaults in this document.** Options are listed for Founder decision only.

---

## FD-1 — Approval object granularity

**Question:** Is Editorial Approval only phase-scoped artifact promotion (2A/2B/3), or also a single content-item approval spanning the week?

| Evidence | Promote copies phase file sets into `input/{week}/`; no content-row approval entity. |
|----------|-------------------------------------------------------------------------------------|
| Option A | Phase-scoped promote only (matches current code) |
| Option B | Content-item approval record that may cover multiple phases |
| Option C | Both (phase promote + overlay content approval) |
| Impact A | Lowest change; CLI remains SoT |
| Impact B/C | Needs persistence model + Lifecycle ADR likely |
| Default | **NOT selected** |

---

## FD-2 — Approver identity & AI enforcement

**Question:** Must Editorial Approver be an authenticated human identity (role/user id), and how is AI-as-approver prevented?

| Evidence | Free-text `--approver`; no ACL; AI could set env string today. |
|----------|----------------------------------------------------------------|
| Option A | Keep free-text human name (ops trust) |
| Option B | Require Shared Platform authenticated user + role |
| Option C | Free-text + deny-list / policy that automation keys cannot promote |
| Impact A | Status quo |
| Impact B | Auth + API surface; Shared Platform dependency |
| Option C | Policy/config work |
| Default | **NOT selected** |

---

## FD-3 — Mandatory readiness / QA before approve

**Question:** Must Editorial Readiness (`validation_passed=true`) and/or tracker `qa_status=PASS` be prerequisites for approval/promote?

| Evidence | Promote uses `validate_staged` for the phase; does not call readiness API or require tracker QA. |
|----------|--------------------------------------------------------------------------------------------------|
| Option A | Keep phase `validate_staged` only |
| Option B | Also require readiness `validation_passed=true` |
| Option C | Also require tracker `qa_status=PASS` |
| Impact | B/C couple Readiness/pipeline to promote; may block ops paths |
| Default | **NOT selected** |

---

## FD-4 — Lifecycle / tracker status for approval

**Question:** Should approval appear as a tracker/content lifecycle state (e.g. Approved), or remain audit+filesystem only?

| Evidence | Promote does not mutate tracker status; CMS stages are reference-only. |
|----------|------------------------------------------------------------------------|
| Option A | No new lifecycle state (audit + `input/` presence only) |
| Option B | New/adapted tracker status for approved — **requires Lifecycle ADR** |
| Option C | Frontmatter `publish_status=approved` as SoT |
| Impact B | Lifecycle ADR + Content Studio/Kanban contract impact |
| Default | **NOT selected** |

---

## FD-5 — Publishing authorization coupling

**Question:** Does Editorial Approval ever authorize Publishing Engine execution?

| Evidence | Promote ≠ publish; go-live/hashnode separate; checklist notes human sign-off. |
|----------|-------------------------------------------------------------------------------|
| Option A | Never — Editorial Approval is editorial-only (ADR interim Decision A) |
| Option B | Approval is necessary but not sufficient for publish |
| Option C | Approval alone may trigger publish automation |
| Impact C | High blast; Publishing Engine redesign |
| Default | **NOT selected** |

---

## FD-6 — Rejection semantics

**Question:** What does rejection mean for Editorial Approval?

| Evidence | No content-promote reject path; Revenue OS reject is unrelated. |
|----------|------------------------------------------------------------------|
| Option A | No formal rejection — only block promote on validation failure |
| Option B | Explicit reject decision with required reason + audit; return to revision (staging) |
| Option C | Reject mutates tracker/lifecycle state |
| Impact B/C | New API/CLI + possibly Lifecycle ADR |
| Default | **NOT selected** |

---

## FD-7 — Revocation / supersession after edit

**Question:** Can approval be revoked or invalidated when canonical `input/` artifacts change after promote?

| Evidence | Backups exist; no revoke API; overwrite via new promote is possible. |
|----------|---------------------------------------------------------------------|
| Option A | Latest successful promote supersedes; no formal revoke |
| Option B | Explicit revoke with audit; artifacts remain until re-promote |
| Option C | Any edit to approved `input/` files auto-invalidates approval |
| Impact C | Needs watchers/hooks or strict process |
| Default | **NOT selected** |

---

## FD-8 — Audit field expansion

**Question:** Which additional audit fields are mandatory beyond current `promotion_audit`?

| Evidence | Audit has approver, UTC time, week, paths, validators, git SHA, notes, backup. No correlation ID / previous decision link / auth user id. |
|----------|------------------------------------------------------------------------------------------------------------------------------------------|
| Option A | Current audit fields sufficient |
| Option B | Add authenticated user id + correlation ID |
| Option C | Add previous decision id / supersession chain |
| Impact B/C | Schema/API design (still no DB mandated here) |
| Default | **NOT selected** |

---

## Summary count

**Founder Decisions Remaining: 8** (FD-1 … FD-8)

Until resolved and ADR amended to **Accepted**, verdict remains:

**FOUNDER DECISIONS REQUIRED BEFORE IMPLEMENTATION**
