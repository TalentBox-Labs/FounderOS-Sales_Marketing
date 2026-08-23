# UI1.1 — Pre-Fix Adversarial Results

**Sprint:** UI1.1  
**Date:** 2026-08-13  
**Environment:** Local pytest fixtures; no production data touched

---

## Methodology

Each bypass was reproduced deterministically before remediation using fixture/test data. Attempt vectors per sprint spec.

---

## UI1-B1 — JWT PUT Contact.status

| Attempt | Pre-fix result |
|---------|----------------|
| Authenticated PUT with `status: qualified` | **EXPLOITABLE** — status changed without `requested_by` |
| Unauthenticated PUT | Blocked by JWT `get_current_user` dependency |
| Spoofed `requested_by` in body | N/A — field not present on JWT schema |
| Direct service call | Separate bypass (UI1-B3) |
| Audit on mutation | **MISSING** |

**Verdict:** MEDIUM bypass confirmed.

---

## UI1-B2 — n8n meeting.booked

| Attempt | Pre-fix result |
|---------|----------------|
| n8n webhook with valid auth + `contact_id` | **EXPLOITABLE** — auto `QUALIFIED` |
| Unauthenticated webhook | Blocked (401 when API key configured) |
| Agent identity | n8n `actor=n8n` performed mutation |
| Human gate | **ABSENT** |
| Audit | Logged but mutation unauthorized |

**Verdict:** MEDIUM bypass confirmed.

---

## UI1-B3 — Service-layer direct call

| Attempt | Pre-fix result |
|---------|----------------|
| `apply_contact_status_update(db, contact, QUALIFIED)` | **EXPLOITABLE** — no authority check |
| `apply_deal_stage_update(db, deal, stage)` | **EXPLOITABLE** — no authority check |
| `accept_qualified_demand(db, id, "agent:hermes")` | **EXPLOITABLE** at service layer (route would block) |
| Spoofed human metadata `"Krishna"` | **EXPLOITABLE** via direct call |
| Runner route with agent `requested_by` | Blocked at route (403) |
| Replay / idempotent accept | Safe — no double mutation |

**Verdict:** LOW bypass confirmed (defense-in-depth gap; no live agent runtime path).

---

## Cross-cutting pre-fix matrix

| Vector | Contact.status | Deal stage | MC04 accept | n8n qualify |
|--------|---------------|------------|-------------|-------------|
| Unauthenticated | BLOCKED (JWT) | BLOCKED | BLOCKED | BLOCKED* |
| Agent direct mutation | **POSSIBLE** (svc/JWT/n8n) | **POSSIBLE** (svc) | **POSSIBLE** (svc) | **POSSIBLE** |
| AI direct mutation | **POSSIBLE** | **POSSIBLE** | **POSSIBLE** | **POSSIBLE** |
| Spoofed human metadata | **POSSIBLE** (svc) | **POSSIBLE** (svc) | **POSSIBLE** (svc) | N/A |
| Valid authorized human (runner) | PASS | PASS | PASS | N/A |
| Audit on unauthorized | FAIL (JWT/n8n) | N/A | N/A | FAIL |

\* n8n open/dev mode when no API key configured.

---

## Governance defect count (pre-fix)

| Severity | Count |
|----------|------:|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 2 |
| LOW | 1 |

Matches UI1 audit.
