# ADR — Editorial Approval Semantics

Filename: `ADR_EDITORIAL_APPROVAL_SEMANTICS.md`  
(Descriptive naming; no numeric ADR sequence under `docs/architecture/adr/`.)

Date: 2026-08-09  
Sprint: E6C — Governance only  
Canonical repository: `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`

Related: [09_APPROVAL_BOUNDARY.md](../../migration/editorial-engine/09_APPROVAL_BOUNDARY.md), [E6B_5_READINESS_BASELINE_FREEZE.md](../../migration/editorial-engine/E6B_5_READINESS_BASELINE_FREEZE.md), [E6C_FOUNDER_DECISIONS.md](../../migration/editorial-engine/E6C_FOUNDER_DECISIONS.md), [ADR_CONTENT_STUDIO_CALENDAR_SEMANTICS.md](ADR_CONTENT_STUDIO_CALENDAR_SEMANTICS.md)

---

# Status

**Accepted** (2026-08-09) — Founder Decisions FDR-001 / FDR-002 / FDR-003 ratified for Sprint E7 Phase 1.

---

# Context

Editorial Readiness Baseline v1.0 is frozen (read-only evidence aggregation). E6A/E6B.5 established:

**APPROVAL ADR REQUIRED**

before any Editorial Engine approval implementation, CMS stage import, or auto-promotion.

Founder already has an executable promotion gate (`promote_staged` + `promotion_audit`). Revenue OS has a separate approve/reject queue for CRM/outreach actions. These must not be conflated.

CMS human-gateway / Sheets stage machine is REFERENCE ONLY and is not Founder SoT.

This ADR defines **Editorial Approval** semantics for Marketing OS → Editorial Engine using repository evidence. Where evidence is insufficient, decisions are deferred to the Founder (see E6C_FOUNDER_DECISIONS.md) — not invented here.

---

# Repository Evidence

1. **`src/tools/promote_staged.py`** — Requires `--approver` or `WORKCREW_PROMOTION_APPROVER`; copies phase-specific staged files into `input/{week}/`; no tracker status mutation; no HTTP promote route.
2. **`src/tools/promotion_audit.py`** — Persists `approver`, UTC timestamp, week_id, staging/canonical paths, validator runs, backup path, git short SHA, notes, skip_validation flag; appends `promotion_history.jsonl`.
3. **`src/tools/validate_staged.py`** — Phase gates (2a/2b/2c/3) normally required before promote (bypass only with force env).
4. **`src/tools/tracker_updater.py`** — Full pipeline sets `status=QA Passed`, `qa_status=PASS` only; not promote; not publish authorization.
5. **`src/tools/publish_checklist_checker.py`** — Structure check; comments that human sign-off still required.
6. **`src/tools/go_live_helpers.py` / `hashnode_publish.py`** — Publishing / go-live recording are separate paths from promote.
7. **`runner_api_routers/editorial.py`** — Readiness is observational; explicitly not approval or publish permission.
8. **`runner_api_routers/approvals.py` + Revenue OS models** — Approve/reject for **non-content** actions (outreach/deals); different domain surface.
9. **Missing** `docs/Artifact_Promotion_PRD.md` (referenced by promote error text) — PRD content **NOT VERIFIED**.
10. **CMS** OpenClaw gateway / Sheets APPROVED stages — REFERENCE ONLY; not Founder executable SoT.
11. **No** `ready_for_publish` field found in Founder repo.
12. **No** content-promote reject CLI/API found.
13. Approver identity for promote is a **free-text string**; no role ACL verified.

---

# Decision

Until Founder decisions below are resolved and this ADR is **Accepted**, implementers MUST treat the following as the **interim canonical Editorial Approval** model (evidence-backed):

> **Editorial Approval = human-attested promotion of a staged artifact bundle into the canonical `input/{week}/` tree via `promote_staged`, audited by `promotion_audit`.**

It is **not**:

- Editorial Readiness `readiness_summary` / `validation_passed`
- Tracker `status=QA Passed` from `/run`
- Revenue OS `/api/v1/approvals` records
- CMS Sheets stage `APPROVED` / OpenClaw gateway
- Authorization to publish or record go-live

Any new HTTP approval API, role model, rejection workflow, or lifecycle state machine requires resolving **FOUNDER DECISION REQUIRED** items and amending this ADR to **Accepted**.

---

# Approval Object

**Decided (evidence):** Phase-scoped **staged artifact bundle** for a `week_id` / `content_id`:

| Phase | Objects copied on promote |
|-------|---------------------------|
| 2A | `01_Content_Brief.md` … `04_Draft.md` |
| 2B | `05_Final.md` |
| 3 | `06_Design_Brief.md` … `09_Publish_Checklist.md` |

**Not decided without Founder input:** whether a single “content item approval” overlays these phase promotions; whether frontmatter `publish_status` values (`approved`, `ready`) constitute Editorial Approval.

→ Partial **FOUNDER DECISION REQUIRED** (see E6C FD-1).

---

# Approval Authority

| Candidate | Classification | Evidence |
|-----------|----------------|----------|
| Human operator (free-text name) | **ALLOWED** (current executable) | `--approver` / `WORKCREW_PROMOTION_APPROVER` |
| Editor role / founder/admin ACL | **NOT DEFINED** | No role check in promote |
| QA agent / AI agent / system automation as approver | **NOT ALLOWED** for Editorial Approval authority under this ADR’s governing intent | Docs intend human; AI may write staging without gate; code does not cryptographically prove humanity — **enforcement** is FOUNDER DECISION (FD-2) |
| Revenue OS `decided_by` | Out of scope for Editorial Approval | Different product surface |

---

# Preconditions

Signals relative to **promote** (current executable), not invented mandates for a future API:

| Signal | Classification |
|--------|----------------|
| Staged files present for phase | CURRENTLY REQUIRED (promote errors if missing) |
| `validate_staged` pass for phase | CURRENTLY REQUIRED unless forced skip (`WORKCREW_PROMOTE_FORCE`) |
| Non-empty approver string | CURRENTLY REQUIRED |
| Draft / final / checklist presence | AVAILABLE BUT OPTIONAL as promote inputs depend on phase |
| Editorial Readiness `validation_passed=true` | AVAILABLE BUT OPTIONAL (read model; not consulted by promote) |
| Tracker `qa_status=PASS` | AVAILABLE BUT OPTIONAL (not consulted by promote) |
| Role-authenticated human | NOT DEFINED |
| Mandatory rejection of prior decision | NOT DEFINED |

Making Readiness or tracker QA **mandatory** for promote → **FOUNDER DECISION REQUIRED** (FD-3).

---

# Lifecycle Effect

**Decided (evidence for current promote):**

- Promote **mutates the filesystem** (staging → `input/`) and writes audit/backup.
- Promote does **not** mutate `tracker.csv` `status` / `qa_status` / `current_step`.
- Pipeline `/run` may set `QA Passed` independently — that is a **validation signal**, not Editorial Approval.

**Do not invent** CMS-style IDEA→…→APPROVED tracker states in this ADR.

If product requires approval as a first-class content lifecycle status:

→ **LIFECYCLE ADR REQUIRED** (and FOUNDER DECISION FD-4).

**Allowed interim pattern (evidence-aligned):** Editorial Approval exists as **promotion audit record + canonical artifact presence**, without new tracker enum values.

---

# Publishing Boundary

**Decided (evidence):**

**A. Editorial Approval means editorially promoted artifacts only — it does NOT authorize Publishing Engine execution.**

Publish / go-live remain separate (`publish_checklist` human note, `hashnode_publish`, `go_live_helpers.record-live` with human URL confirmation).

Conflating promote with publish authorization → **FOUNDER DECISION REQUIRED** (FD-5) and would amend this ADR.

---

# Rejection

**Content promote rejection:** **NOT DEFINED** in Founder executable path (no reject CLI/API; failed validation simply blocks promote).

Revenue OS `reject` applies to CRM actions only — **not** Editorial Approval.

Checklist/QA `FAIL` verdicts are validation outcomes, not formal rejection of an approval decision.

→ **FOUNDER DECISION REQUIRED** for rejection semantics (FD-6).

---

# Revocation / Supersession

| Topic | Evidence | Classification |
|-------|----------|----------------|
| Backup on promote | `.promotion_backup/` path recorded in audit | IMPLEMENTED (rollback aid) |
| Formal revoke API | None | NOT DEFINED |
| Supersession by new promote | New promote can overwrite `input/` files; new audit event | PARTIAL (implicit supersession) |
| Invalidation after edit of canonical files | No automatic invalidation | NOT DEFINED |

→ **FOUNDER DECISION REQUIRED** (FD-7).

---

# Audit Requirements

**Minimum semantics already supported by promotion_audit (required for any Editorial Approval implementation):**

| Field | Current support |
|-------|-----------------|
| Approver identity | `approver` string |
| Timestamp | `utc_timestamp` (UTC) |
| Content/week identity | `week_id` |
| Decision / event | `event` name |
| Reason / notes | `notes` (optional today) |
| Artifact scope | staging_root, canonical_dir, diffs |
| Validator evidence | `validators` runs |
| Correlation / source | `git_commit_short`; no dedicated correlation ID |
| Previous decision link | NOT DEFINED (history JSONL is chronological only) |

Additional fields (authenticated user id, correlation ID, previous decision id) → **FOUNDER DECISION REQUIRED** (FD-8) — do not design schema in this ADR.

---

# AI / Human Boundary

| Action | Classification |
|--------|----------------|
| AI may generate/edit **staging** artifacts | ALLOWED (existing crews) |
| AI may mark / compute **readiness** evidence | ALLOWED (validators + readiness read model; observational) |
| AI may **recommend** promote | NOT DEFINED (no formal recommend API) |
| AI may **approve** (act as Editorial Approver) | **NOT ALLOWED** under this ADR |
| AI may **publish** after approval | **NOT ALLOWED** as automatic consequence of Editorial Approval; Publishing Engine remains separate with its own human confirmations |

Auto-approve patterns in Revenue OS / DecisionManager **do not** grant Editorial Approval authority.

---

# Domain Ownership

| Concern | Owner |
|---------|-------|
| Editorial Approval (promote attestation + audit) | **Editorial Engine** |
| QA / validation results | **Editorial Engine** (tools + optional QACrew; AI Platform supplies runtime) |
| Publishing authorization / go-live / Hashnode | **Publishing Engine** |
| Revenue OS action approve/reject | **OTHER EXISTING FOUNDER DOMAIN** (Revenue OS) — not Editorial Approval |
| AuthN for future HTTP approval | **Shared Platform** |

---

# Consequences

### Positive

- Clear separation: Readiness ≠ Approval ≠ Publish.
- Preserves existing `promote_staged` / `promotion_audit` as interim SoT.
- Blocks accidental import of CMS Sheets approval or Revenue OS approvals into content promote.

### Negative / deferred

- No HTTP Editorial Approval API until Founder decisions resolved.
- Rejection/revoke/role ACL remain unspecified.
- Tracker lifecycle still lacks an “approved” state (by design until Lifecycle ADR).

---

# Explicit Non-Goals

This ADR does **not** authorize:

- Implementing approval/reject HTTP APIs
- Changing promote behavior
- Auto-promotion without human approver
- Treating readiness or `QA Passed` as approval
- CMS stage machine import
- Publishing mutation or go-live changes
- Database schema for approvals
- Prompt/Crew changes
- Granting AI Editorial Approval authority

---

# Deferred Decisions

See [E6C_FOUNDER_DECISIONS.md](../../migration/editorial-engine/E6C_FOUNDER_DECISIONS.md) (FD-1 … FD-8).

Also deferred: Calendar (E5A), CMS ritual parity, `/edit`/`/generate` staging fixes (orthogonal).

---

# Implementation Readiness

**FOUNDER DECISIONS REQUIRED BEFORE IMPLEMENTATION**

of any **new** Editorial Approval product slice (HTTP API, UI approve/reject, lifecycle status).

Existing CLI `promote_staged` may continue as the interim operational mechanism under this PROPOSED ADR without code change in E6C.
