# A4 — Authority & Security Audit (SENTINEL)

**Sprint:** SALES A4  
**Role:** Human Authority Auditor  
**Date:** 2026-08-13  
**Scope:** `Contact.status` mutation paths — who can write today, gaps vs frozen authority contract, required A4 enforcement.

**Binding references:**

- [SALES_AGENT_AUTHORITY_CONTRACT_v1.0.md](../SALES_AGENT_AUTHORITY_CONTRACT_v1.0.md) — frozen; qualification = **HUMAN_ONLY**; LeadScorer auto-status = **known gap**
- [SALES_AGENT_AUTHORITY_MATRIX.md](../SALES_AGENT_AUTHORITY_MATRIX.md) — scoring may recommend; status promotion requires human
- [A3_SECURITY_AND_AUTHORITY_AUDIT.md](../a3/A3_SECURITY_AND_AUTHORITY_AUDIT.md) — A3 pattern for `Deal.stage`
- [A3_5_AUTHORITY_SECURITY_ATTESTATION.md](../a3_5/A3_5_AUTHORITY_SECURITY_ATTESTATION.md) — attested controls for deal stage
- `src/tools/editorial_approval.py` — `is_human_approver` (FDR-002)

---

## Executive verdict

| Control | Current state | A4 target |
|---------|---------------|-----------|
| Human-only qualification (`Contact.status` write) | **FAIL** — six autonomous/agent paths mutate status | **HUMAN_ONLY** |
| Agents may score only (no status write) | **FAIL** — `LeadScorer.update_contact_status` couples score → status | Score write only; status = recommendation |
| `is_human_approver` on status mutation | **NOT APPLIED** (only on `Deal.stage` A3 path) | Required on canonical status endpoint |
| Actor audit on status change | **PARTIAL** — some paths log to `agent_action_log`; API writes do not record human identity | `requested_by` + EventBus payload |

**Authority debt confirmed:** A4 closes the frozen gap named in A1.5 §4 (`LeadScorer auto status`) and extends the A3 human-gate pattern from pipeline stage to contact qualification.

---

## A3 pattern baseline (reference — not applied to Contact.status)

Deal stage mutation on the runner CRM path is the model A4 should mirror:

| Layer | A3 (`Deal.stage`) | A4 gap (`Contact.status`) |
|-------|-------------------|---------------------------|
| Endpoint | `PATCH /api/v1/crm/deals/{deal_id}/stage` | **No dedicated human-gated status endpoint** |
| Auth | `_verify_api_key` Bearer | Mixed: API key (runner CRM create), JWT (revenue API PUT), shared secret (n8n) |
| Human gate | `requested_by` + `is_human_approver()` → 403 | **Absent** on all status write paths |
| Service | `apply_deal_stage_update` | Status writes scattered across services |
| Audit | EventBus `DEAL_STAGE_CHANGED` + `requested_by` | Inconsistent; auto paths use `agent_action_log` only |

### `is_human_approver` semantics (editorial_approval / FDR-002)

```python
# src/tools/editorial_approval.py — summary
# - Requires non-empty human name (len >= 2)
# - Rejects forbidden tokens: ai, agent, bot, automation, system, llm, gpt, claude, …
# - Rejects prefixes: ai:, agent:, bot:
```

**Current usage:** imported only in `runner_api_routers/crm.py` for deal stage updates. **Not used** for any `Contact.status` path.

---

## Contact.status domain

Enum (`revenue_os/models/contact.py`): `lead`, `prospect`, `qualified`, `customer`, `churned`, `partner`, `candidate`, `vendor`.

Qualification-relevant transitions (A4 focus): any change among `lead` / `prospect` / `qualified`, plus promotion to `customer` (commercial lifecycle). All are **HUMAN_ONLY** per authority contract §3.

---

## Current mutation paths (inventory)

### 1. Human-operable API paths (no `is_human_approver`)

| Path | File | Auth | Can set/change `status`? | Human identity captured? |
|------|------|------|--------------------------|--------------------------|
| `POST /api/v1/crm/contacts` | `runner_api_routers/crm.py` | API key (optional in dev) | **Yes** — `ContactCreateRequest.status` (default `prospect`) | **No** |
| `POST /api/v1/contacts` | `revenue_os/api/v1/contacts.py` | JWT (`get_current_user`) | **Yes** — `ContactCreate.status` (default `LEAD`) | User ID in JWT only; not qualification audit |
| `PUT /api/v1/contacts/{contact_id}` | `revenue_os/api/v1/contacts.py` | JWT | **Yes** — `ContactUpdate.status` via generic `setattr` loop | **No** `requested_by`; no forbidden-identity check |

**UI exposure:** `frontend/src/pages/Contacts.jsx` creates contacts via runner CRM with a status dropdown. `ContactDetail.jsx` displays status read-only — no edit control, but JWT PUT remains callable by any authenticated client.

**Gap:** API key or JWT proves *operator session*, not *human qualification decision*. Same residual impersonation risk as A3 (accepted for deal stage); status path lacks even the A3 `requested_by` field.

---

### 2. Autonomous scoring → status promotion (authority violation)

#### 2a. `LeadScorer.update_contact_status` (primary offender)

| Caller | File | Trigger | Auth / actor |
|--------|------|---------|--------------|
| `score_contact` / `score_contacts_batch` | `revenue_os/services/lead_scoring_service.py` | Score thresholds: ≥70 → `qualified`, ≥40 → `prospect`, else `lead` | N/A (service layer) |
| `POST /api/v1/hermes/score-contacts` | `runner_api_routers/hermes.py` | HTTP batch score | API key; actor implicit = caller with key |
| Heartbeat `job_score_new_leads` | `revenue_os/scheduler.py` | Hourly (default 3600s) | `actor="heartbeat"` |
| Hermes planner `action_score_unscored_leads` | `revenue_os/services/hermes_planner.py` | Goal-driven plan step | `actor="hermes"` |

**Behavior:** every score run **writes** `contact.lead_score` **and** mutates `contact.status` without human approval.

#### 2b. Hermes planner direct qualification

| Action | File | Behavior |
|--------|------|----------|
| `action_qualify_high_scorers` | `revenue_os/services/hermes_planner.py` | Sets `contact.status = QUALIFIED` for `lead_score >= threshold` (default 70); emits `LEAD_QUALIFIED`; files outreach approvals separately |

**Gap:** status promotion is **not** behind the approval queue — only downstream email send is.

#### 2c. Legacy Celery task

| Task | File | Behavior |
|------|------|----------|
| `enrich_lead` | `revenue_os/tasks/leads.py` | Uses `scoring_service.score_contact` (score only), then **if score ≥ 50 and status == LEAD → QUALIFIED** |

**Note:** dual scorer conflict documented in A0 — `scoring_service.score_contact` does not auto-mutate status, but this task adds a second autonomous promotion rule.

---

### 3. Automation / n8n inbound (authority violation)

| Event | File | Behavior | Auth |
|-------|------|----------|------|
| `meeting.booked` | `runner_api_routers/n8n_webhooks.py` | `contact.status = QUALIFIED`; emits `LEAD_QUALIFIED` | Bearer API key or `X-N8N-Secret` |

**Catalog documents intent:** *"Contact status -> qualified"*. No human gate; actor logged as `n8n` in `agent_action_log`.

Other n8n events (`email.replied`) bump `lead_score` only — **no status write** (acceptable scoring signal).

---

### 4. Paths that read status but do not mutate

| Component | File | Role |
|-----------|------|------|
| `scoring_service.score_contact` | `revenue_os/services/scoring_service.py` | Updates `lead_score` only; uses status as score **input** |
| `create_contact` post-score | `revenue_os/api/v1/contacts.py` | Calls legacy scorer after create — no status side effect |
| Hermes/deal automation | `deal_automation_service.py`, `hermes.py` | **Reads** `contact.status == QUALIFIED` as precondition |
| Analytics / command center | various | Read-only filters |

---

### 5. Dormant / non-runtime paths

| Path | File | Notes |
|------|------|-------|
| `bulk_upsert_contacts` | `revenue_os/services/contact_service.py` | Generic `setattr` including `status` — **no callers** in repo |
| `scripts/init_demo_db.py` | seed script | Dev/demo only |

---

## Who CAN mutate `Contact.status` today

| Actor class | Mechanism | Human gate? | Compliant? |
|-------------|-----------|-------------|------------|
| **Authenticated human (JWT)** | `PUT /api/v1/contacts/{id}` | No `requested_by` / `is_human_approver` | Partial — human likely, not enforced |
| **Operator with API key** | `POST /api/v1/crm/contacts` (initial status) | No | Partial |
| **Hermes agent / planner** | `action_qualify_high_scorers`, scoring side effects | No | **No** |
| **Heartbeat scheduler** | `job_score_new_leads` → LeadScorer | No | **No** |
| **Hermes API client** | `POST /api/v1/hermes/score-contacts` | No | **No** |
| **n8n automation** | `POST /webhooks/n8n/meeting.booked` | No | **No** |
| **Celery worker** | `enrich_lead` task | No | **No** |
| **Sales UI agents (SDR crew)** | Draft/approval flows on contact detail | Do not mutate status directly | **Yes** (read/draft only) |

**Summary:** Any holder of the runner API key, n8n secret, or JWT can change status through API or trigger autonomous promotion through scoring, heartbeat, Hermes goals, or calendar webhooks — **without** `is_human_approver`.

---

## Security gaps (prioritized)

| ID | Gap | Severity | Authority class violated |
|----|-----|----------|--------------------------|
| G1 | `LeadScorer.update_contact_status` auto-writes on every score | **Critical** | HUMAN_ONLY (qualification) |
| G2 | Hermes `action_qualify_high_scorers` bypasses human gate | **Critical** | HUMAN_ONLY |
| G3 | n8n `meeting.booked` hard-sets `qualified` | **High** | HUMAN_ONLY — meeting ≠ human qualification decision |
| G4 | Celery `enrich_lead` score-based promotion | **High** | HUMAN_ONLY |
| G5 | JWT `PUT /contacts` generic status field | **High** | HUMAN_ONLY — no dedicated gate |
| G6 | Runner CRM create accepts arbitrary initial `status` | **Medium** | Bypasses funnel semantics at ingest |
| G7 | No canonical audited status endpoint on runner | **High** | Parity with A3 deal stage |
| G8 | Dual scorers (`scoring_service` vs `lead_scoring_service`) | **Medium** | Confusion; mixed mutation behavior |
| G9 | API key ≠ human identity (shared secret) | **Medium** (accepted residual) | Same as A3 — mitigated only by `requested_by` (missing here) |

---

## What A4 must enforce

### Binding rules

1. **HUMAN_ONLY for `Contact.status` mutation** — any transition among qualification states (`lead` ↔ `prospect` ↔ `qualified`) and promotion to `customer` / `churned` requires an explicit human-gated write path.
2. **Agents may score only** — autonomous actors (`hermes`, `heartbeat`, `n8n`, Celery, LLM tools) may update `lead_score` and emit **recommendations**; they **must not** persist `Contact.status` changes.
3. **Reuse A3 gate primitive** — `is_human_approver(requested_by)` on the canonical mutation endpoint; forbidden identities (`ai`, `agent`, `bot`, `system`, …) → **403**.
4. **Single write funnel** — all intentional status changes flow through one service function (mirror `apply_deal_stage_update`).
5. **Audit** — EventBus event (e.g. `CONTACT_STATUS_CHANGED`) including `old_status`, `new_status`, `requested_by`, optional `notes`; align with `agent_action_log` for automation attempts blocked or redirected.

### Required code changes (A4 scope — not implemented in this audit)

| Change | Target |
|--------|--------|
| Remove status writes from `LeadScorer.update_contact_status` | `revenue_os/services/lead_scoring_service.py` — score only; add `suggested_status` or event payload |
| Disable `action_qualify_high_scorers` status mutation | `hermes_planner.py` — recommend + approval or human endpoint only |
| Change n8n `meeting.booked` | Score boost + `status_recommendation` event; **no** direct `qualified` write |
| Remove Celery status promotion | `revenue_os/tasks/leads.py` |
| Strip `status` from ungated `ContactUpdate` / block in PUT | `revenue_os/api/v1/contacts.py` |
| Add human-gated runner endpoint | `runner_api_routers/crm.py` |
| Consolidate scoring entry points | Prefer one scorer; document legacy path deprecation |

### Out of scope (explicit)

- JWT stack rewrite (same A3 boundary)
- HubSpot / external CRM sync
- New DB migration unless `suggested_status` column chosen (prefer event-only recommendation first)

---

## Recommended gate mechanism

Mirror A3 deal-stage contract for contact qualification status.

### Canonical endpoint (runner — primary UI path)

```
PATCH /api/v1/crm/contacts/{contact_id}/status
Authorization: Bearer <RUNNER_API_KEY>

{
  "status": "qualified",
  "requested_by": "Krishna",
  "notes": "Discovery call completed; SQL criteria met"
}
```

**Handler checks (ordered):**

1. `_verify_api_key` → 401 if key configured and missing/invalid  
2. `is_human_approver(requested_by)` → 403 if automation identity  
3. Validate `status` enum and allowed transitions (define transition matrix; same-stage → no-op success)  
4. `apply_contact_status_update(db, contact, new_status, requested_by, notes)` — sole DB writer  
5. EventBus `CONTACT_STATUS_CHANGED` with full audit payload  
6. Return `{ ok, changed, old_status, new_status, requested_by, contact }`

### Service layer

```text
apply_contact_status_update(db, contact, new_status, *, requested_by, notes)
  - Only function allowed to assign contact.status in runtime code paths
  - Raises ValueError on invalid transition (→ 422)
  - Does not emit CommercialOutcome (Revenue boundary unchanged)
```

### Scoring layer (agents)

```text
score_contact(db, contact) → { lead_score, suggested_status, score_factors }
  - Writes lead_score only
  - suggested_status is advisory (response body + optional EventType.LEAD_SCORED payload)
  - Hermes / heartbeat / n8n / Celery call this path; never call apply_contact_status_update
```

### n8n `meeting.booked` ( revised )

```text
POST /webhooks/n8n/meeting.booked
  → lead_score += N (optional)
  → EventBus LEAD_SCORED or MEETING_BOOKED with suggested_status: "qualified"
  → NO contact.status write
  → Human promotes via PATCH .../status when ready
```

### Legacy JWT API

- **Minimum:** reject `status` in `PUT /contacts/{id}` with 403 directing clients to runner PATCH  
- **Or:** accept PUT only when extended with `requested_by` + same gate (prefer single canonical path)

### Transition policy (recommended default)

| From \\ To | lead | prospect | qualified | customer | churned |
|------------|------|----------|-----------|----------|---------|
| lead | no-op | allow | allow | allow | allow |
| prospect | allow (downgrade) | no-op | allow | allow | allow |
| qualified | allow (downgrade) | allow | no-op | allow | allow |
| customer | — | — | — | no-op | allow |
| churned | allow (re-engage) | allow | allow | allow | no-op |

Downgrades remain **HUMAN_ONLY** — founder may correct mis-qualification.

### Test contract (A4 attestation target)

Mirror `tests/test_a3_runner_deal_stage.py`:

- 401 without/wrong API key  
- 403 for `requested_by=agent`, `ai:foo`, `bot`, empty  
- 200/422 for valid/invalid transitions  
- Scoring endpoints do not change DB status (assert before/after)  
- n8n meeting.booked does not mutate status  
- EventBus payload contains `requested_by`

---

## Comparison: A3 (done) vs A4 (required)

| Dimension | Deal.stage (A3) | Contact.status (A4) |
|-----------|-----------------|---------------------|
| Classification | HUMAN_ONLY | HUMAN_ONLY |
| Gate function | `is_human_approver` | **Must add** |
| Autonomous mutation | Blocked on runner path | **Six paths still open** |
| Agent scoring | N/A | **Must decouple from status write** |
| Frozen contract | A3.5 attested PASS | **Known gap — A4 remediates** |

---

## SENTINEL attestation (pre-A4)

| Check | Result |
|-------|--------|
| All mutation paths enumerated | **PASS** |
| A3 pattern identified for reuse | **PASS** |
| Autonomous status promotion documented | **PASS** |
| Human-only requirement stated | **PASS** |
| Gate mechanism specified | **PASS** |
| Implementation | **NOT STARTED** — audit only |

**Post-A4 pass criteria:** zero runtime code paths assign `contact.status` except `apply_contact_status_update` behind `is_human_approver`; agents limited to score + recommend.

---

*SENTINEL — SALES A4 Human Authority Audit. Evidence: static analysis of `runner_api_routers/*`, `revenue_os/services/*`, `revenue_os/api/v1/contacts.py`, `src/tools/editorial_approval.py`, `revenue_os/scheduler.py`, frozen authority contracts A1.5 / A3.*
