# S0 — Measurement Boundary (Social S1)

**Sprint:** SOCIAL S0  
**Agent:** PULSE  
**Date:** 2026-08-11  
**P1:** Measurement Readiness = PARTIAL

---

## S1 operational measurements (CORE — no analytics engine)

| Metric | Source | Blocker for publish? |
|--------|--------|----------------------|
| publish requested | Publishing job create | No — implement with job |
| publish accepted / dispatched | Publishing → adapter | No |
| publish succeeded | Adapter result + job state | No |
| publish failed | Adapter error + job state | No |
| external_post_id | Provider response | No |
| timestamp | Job / audit | No |
| retry count | Publishing attempts | No |
| normalized error | Adapter | No |

These can live in existing Publishing audit JSONL + job records.

**Class:** REPO VERIFIED that Publishing already audits job transitions; Social-specific fields ASSUMPTION until adapter lands.

---

## Deferred marketing analytics

| Metric | Requires | S1 |
|--------|----------|-----|
| Impressions / reach | LinkedIn analytics endpoints + scopes | DEFERRED |
| Engagement (likes/comments) | Analytics / social actions APIs | DEFERRED |
| Clicks | Analytics or UTM on own site | DEFERRED |
| Followers / leads / conversions | Broader stack | DEFERRED |

`r_member_social` is **restricted** per Posts API permissions docs — do **not** treat analytics as S1 publish blocker.

---

## Measurement readiness

**PARTIAL** — operational publish telemetry design is clear; marketing analytics not in S1 and not a GO gate for Manual Publisher.
