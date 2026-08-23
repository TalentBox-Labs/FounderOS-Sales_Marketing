# A3.5 — Authority & Security Attestation (SENTINEL)

**Sprint:** SALES A3.5  
**Date:** 2026-08-13  
**Evidence:** `tests/test_a3_runner_deal_stage.py` (15/15)

| Control | Attestation |
|---------|-------------|
| Authentication (`_verify_api_key`) | **PASS** — 401 without/wrong Bearer when key set |
| HUMAN_ONLY (`is_human_approver`) | **PASS** — required `requested_by` |
| Agent mutation (`agent`, `ai:…`) | **BLOCKED** 403 |
| Unauthorized key | **BLOCKED** 401 |
| Direct runner API (no UI) | Allowed only with human + auth — **PASS** |
| Requester in audit EventBus data | **PASS** |
| Credential commit | **NONE** observed in A3/A3.5 |
| Autonomous AI deal-stage route | **NONE** on runner path |

**Human-Only Authority Contract: FROZEN**  
**Agent Mutation Prohibition: FROZEN**  
**Authentication Contract: FROZEN**
