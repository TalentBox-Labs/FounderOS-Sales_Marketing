# UI1.1 — Post-Fix Adversarial Results

**Sprint:** UI1.1  
**Date:** 2026-08-13  
**Test suite:** `tests/test_ui1_1_mutation_authority.py` + focused A3/A4/MC04 suites

---

## Bypass closure verification

| Bypass | Post-fix result | Status |
|--------|-----------------|--------|
| UI1-B1 JWT PUT status | 403; status unchanged | **CLOSED** |
| UI1-B2 n8n meeting.booked | No status write; recommendation event only | **CLOSED** |
| UI1-B3 service direct call | `HumanAuthorityError` on agent/spoofed identity | **CLOSED** |

**Mutation bypasses closed: 3/3**

---

## Required proof matrix

| Vector | Result |
|--------|--------|
| Agent direct mutation | **BLOCKED** |
| AI direct mutation | **BLOCKED** |
| Automation direct mutation (HUMAN_ONLY) | **BLOCKED** |
| Spoofed human metadata (`agent:hermes`) | **BLOCKED** |
| Unauthenticated mutation (runner) | **BLOCKED** |
| Unauthorized human (forbidden names) | **BLOCKED** |
| Valid authorized human (`Krishna Sales`) | **PASS** |
| Audit integrity | **PASS** (runner routes emit events; MC04 AgentActionLog) |
| State integrity | **PASS** (failed mutations leave no partial CRM state) |

---

## Test evidence

| Test | Result |
|------|--------|
| `test_jwt_put_contact_status_change_blocked` | PASS |
| `test_n8n_meeting_booked_does_not_mutate_status` | PASS |
| `test_service_contact_status_blocks_agent_direct_call` | PASS |
| `test_service_deal_stage_blocks_agent_direct_call` | PASS |
| `test_service_accept_demand_blocks_spoofed_automation` | PASS |
| `test_service_reject_demand_blocks_automation_identity` | PASS |
| `test_service_human_mutation_succeeds` | PASS |
| `test_runner_contact_status_blocks_spoofed_human` | PASS |
| `test_runner_contact_status_valid_human_passes` | PASS |

**Focused UI1.1 + A3 + A4 + MC04:** 51/51 passed

---

## Governance defects remaining

| Severity | Count |
|----------|------:|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 0 |

---

## Verdict

All pre-fix bypass attempts **CLOSED**. Human-only mutation boundaries enforced at canonical service layer.
