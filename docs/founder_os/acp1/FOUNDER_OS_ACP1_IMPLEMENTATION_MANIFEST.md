# Founder OS ACP-1 — Implementation Manifest

| Item | Value |
|------|-------|
| Sprint | ACP-1 — Agent Control Plane Foundation (Authority & Tenant Hardening) |
| New persistent SoTs | 0 |
| New models | 0 |
| Migrations | 0 |
| Frozen tests modified | 0 |
| Authority widening | NO |
| Outbound widening | NO |
| Booking widening | NO |

## Files changed

### Created
- `revenue_os/services/acp1_autonomous_boundary.py`
- `tests/test_founder_os_acp1_authority_tenant_hardening.py`
- `docs/founder_os/acp1/*` (this set)

### Modified
- `revenue_os/scheduler.py` — per-org commercial jobs; fail closed without tenants
- `revenue_os/services/hermes_planner.py` — org-required actions; Deal create blocked
- `revenue_os/services/follow_up_eligibility.py` — `scan_eligible_follow_ups` requires `organization_id`
- `revenue_os/services/deal_automation_service.py` — stamp `Deal.organization_id` from Contact
- `revenue_os/integrations/gmail_sync.py` — require `organization_ids`; scoped Contact match

### Not modified
- `activity_log.py` (existing `status` + `organization_id` sufficient)
- COS-1…5 / tenant remediation / MC04 / UI-D* / S2.5–S3 frozen tests
