# ADR — Content Studio Calendar Semantics (Read-Only)

Filename: `ADR_CONTENT_STUDIO_CALENDAR_SEMANTICS.md`  
(No prior ADR numbering convention found under `docs/architecture/adr/`; descriptive name used.)

Date: 2026-08-09  
Sprint: E5A  
Canonical repository: `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`

Audit evidence: [E5A_CALENDAR_DATA_AUDIT.md](../../migration/content-studio/E5A_CALENDAR_DATA_AUDIT.md)

---

# Status

**PROPOSED**

---

# Context

Content Studio Kanban Baseline v1.0 is frozen. The next planned visualization is a read-only Content Studio Calendar. Sprint E4.5 correctly gated:

**CALENDAR REQUIRES DATA/SEMANTIC ADR**

CMS (`workcrew-cms-os`) historically showed a calendar intended to place items by Sheets `publish_date`. Founder must not adopt CMS/Sheets assumptions without Founder-canonical evidence.

This ADR covers **read-only visualization semantics only**.

---

# Repository Evidence

1. **Content Studio API** (`runner_api_routers/content_studio.py`) serializes tracker columns only — **no date fields**.
2. **`tracker.csv`** header has **no** `publish_date`, `scheduled_at`, `due_date`, or similar.
3. **Live frontmatter** (`input/*/05_Final.md`) includes `publish_status` / `status` but **no** `publish_date` (repo-wide search empty).
4. **`src/tools/sheet_sync.py`** can read optional FM `publish_date` into Sheets “Publish Date”, but that is a sync mirror path; live FM values are empty.
5. **Week ids** (`W01`…) and programme labels (`M1/Wk1`) are **period identifiers**, not calendar dates. No authoritative W## → date map exists in Founder SoT.
6. **Postgres** `published_at` / `scheduled_at` on social/library models are **not wired** to Content Studio.
7. **Timezone:** Celery/ops use UTC; Content Studio calendar timezone is **NOT VERIFIED** (no APP local TZ; no live content dates).
8. **CMS calendar** depended on Sheets and shipped a non-authoritative demo template — reference UX only.

---

# Decision

**A read-only Content Studio Calendar cannot yet be implemented safely.**

Canonical calendar semantic for Content Studio:

**NOT ESTABLISHED**

Canonical date source for Content Studio Calendar:

**NOT VERIFIED** — no populated Founder-canonical date field is exposed on the Content Studio read model.

Therefore:

1. **Do not** implement E5B Calendar UI against invented mappings (including W## → calendar date).
2. **Do not** treat Google Sheets “Publish Date” as Founder Content Studio source of truth.
3. **Do not** treat filesystem mtimes, Obsidian `created`, or social Postgres timestamps as the Content Studio calendar axis without a separate product ADR that explicitly rebinds those surfaces.
4. **WEEK IDENTIFIER IS NOT A CALENDAR DATE.**
5. Optional frontmatter `publish_date` remains a **candidate** future source **only after**:
   - values are present for content that should appear on a calendar,
   - semantic is declared (scheduled publish vs actual publish — currently **NOT VERIFIED**),
   - Content Studio read API (or an approved equivalent Founder read path) exposes the field,
   - and a follow-on ADR or ADR amendment **Accepts** that contract.

Until those conditions hold, Calendar UI is **blocked**.

---

# Consequences

### Positive

- Prevents fabricated calendar semantics and dual SoT (Sheets vs Founder).
- Preserves Kanban/list/detail baselines without lifecycle redesign.
- Forces an explicit data contract before UI spend.

### Negative / deferred

- No Content Studio Calendar in the product until data/semantics are established.
- CMS calendar parity is not achievable from current Founder CS evidence.

### Required follow-on (outside E5B UI)

Choose and populate one Founder-canonical date axis (preferred candidates, not approved here):

- Contracted, populated `05_Final.md` `publish_date` (or per-id override) exposed on CS read API, **or**
- New tracker column with ADR-defined meaning,

…then amend this ADR to **Accepted** with the chosen semantic before E5B.

Timezone for any future scheduled/publishing operations remains an open ADR issue (**NOT VERIFIED** for content calendar).

---

# Explicit Non-Goals

This ADR does **not** authorize:

- scheduling
- publishing mutation
- drag/drop
- date editing
- campaign mutation
- database migration
- lifecycle/stage redesign
- Sheets as Content Studio SoT
- Celery beat / publish automation for Marketing weeks
- implementation of Calendar UI (E5B)

---

# E5B Gate

| Criterion | Result |
|-----------|--------|
| Canonical date source | FAIL |
| Explicit semantics | FAIL |
| No new DB field required for safe UI | FAIL (no usable axis without new/contracted data) |
| No new lifecycle meaning | PASS only by **not** building Calendar |
| No mutation | N/A — UI blocked |

**E5B Read-Only Calendar: BLOCKED**
