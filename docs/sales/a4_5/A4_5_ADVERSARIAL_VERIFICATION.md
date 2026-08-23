# A4.5 — Adversarial Contract Verification (SENTINEL)

**Sprint:** SALES A4.5  
**Date:** 2026-08-13  
**Method:** Re-run `tests/test_a4_runner_contact_status.py` (15/15) + static path analysis

---

## Contract verification matrix

| # | Case | Result |
|---|------|--------|
| 1 | Score generation succeeds | **PASS** |
| 2 | Score does not mutate state | **PASS** |
| 3 | Authorized human valid mutation | **PASS** |
| 4 | Unauthenticated rejected | **PASS** (401 when key set) |
| 5 | Unauthorized human | N/A — free-text human names accepted per FDR-002 |
| 6 | AI requester rejected | **PASS** (403 `ai:copilot`) |
| 7 | Agent requester rejected | **PASS** (403 `agent`) |
| 8 | Automation requester rejected | **PASS** (403 `bot`) |
| 9 | Spoofed requester type | **PASS** (403 prefixes) |
| 10 | Malformed Contact ID | **PASS** (422) |
| 11 | Nonexistent Contact | **PASS** (404) |
| 12 | Invalid Contact.status | **PASS** (422) |
| 13 | Same-status deterministic | **PASS** (`changed: False`) |
| 14 | Successful mutation audit | **PASS** (`CONTACT_STATUS_CHANGED` event) |
| 15 | Failed mutation no false audit | **PASS** (403/422 no success event) |
| 16 | Marketing unchanged | **PASS** |
| 17 | Revenue deal state unchanged | **PASS** |
| 18 | No external integration | **PASS** |

---

## Direct boundary bypass analysis

| Path | Can agent mutate Contact.status? | Verdict |
|------|----------------------------------|---------|
| Runner `PATCH .../status` without human | **NO** — 403 | **PASS** |
| Runner `POST .../score` | **NO** — score only | **PASS** |
| `score_contact` / Hermes batch | **NO** — score only | **PASS** |
| Hermes planner `action_qualify_high_scorers` | **NO** — recommendation only | **PASS** |
| Heartbeat `job_score_new_leads` | **NO** — score only | **PASS** |
| Celery `enrich_lead` | **NO** — auto-promotion removed | **PASS** |
| Direct `apply_contact_status_update()` call | Possible programmatically (internal service API) | Same pattern as A3 `apply_deal_stage_update`; **no agent runtime path invokes it** |

**Direct Mutation Boundary Verification: PASS** — authoritative LeadScorer/agent paths cannot mutate status; human gate enforced at runner mutation endpoint.

---

## Residual (pre-A4, documented)

| Path | Status |
|------|--------|
| JWT contacts API | Ungated — deferred |
| n8n meeting.booked | Ungated — deferred |

Not LeadScorer-path failures; do not block A4.5 freeze.

---

## Verdict

**PASS** — no successful non-human mutation via A4 LeadScorer/score/agent paths.
