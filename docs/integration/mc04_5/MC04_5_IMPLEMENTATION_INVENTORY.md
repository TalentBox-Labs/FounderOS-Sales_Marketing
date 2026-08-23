# MC04.5 — Implementation Inventory (NOVA / ATLAS)

**Sprint:** FOUNDER OS MC04.5  
**Date:** 2026-08-13  
**Mode:** Baseline freeze verification — **no runtime changes**

---

## MC04 artifacts

### RUNTIME

| Path | Role |
|------|------|
| `revenue_os/services/qualified_demand_service.py` | Handoff register, accept, reject; idempotency; Contact create/merge |

### API

| Path | Role |
|------|------|
| `runner_api_routers/qualified_demand.py` | Marketing handoff + Sales intake routes |
| `runner_api.py` | Router registration |

### DOMAIN

| Model | Role |
|-------|------|
| `Contact`, `Company`, `ContactSource`, `ContactStatus` | Canonical Sales SoT (Revenue) |
| `QualifiedDemandPayload` | Handoff contract validation |

### AUDIT

| Mechanism | Role |
|-----------|------|
| `AgentActionLog` | Handoff / accept / reject records; idempotency via `target_id=demand_id` |
| `EventBus` | Supplementary events on handoff/accept/reject |

### TEST

| Path | Result at freeze |
|------|------------------|
| `tests/test_mc04_qualified_demand.py` | 12/12 |

### DOCUMENTATION (MC04)

| Path | Role |
|------|------|
| `docs/integration/mc04/*` | Implementation attestation pack |

### CONFIGURATION

None.

---

## Behavioral map

| Concern | Implementation |
|---------|----------------|
| Handoff entry | `POST /api/v1/marketing/qualified-demand/handoff` |
| Marketing source | Operator payload stored in audit; **no CRM write** |
| Sales intake | `POST /api/v1/sales/intake/demand/accept|reject` |
| Canonical model | Revenue `Contact` (+ optional `Company`) |
| Idempotency | `AgentActionLog` query by `action_type` + `demand_id` |
| Duplicate email | Merge existing Contact; no silent duplicate |
| Audit | `qualified_demand_handoff` / `_accepted` / `_rejected` |
| Provenance | JSON in Contact `notes`; full payload in handoff audit |
| Authorization | `_verify_api_key` + `is_human_approver` on all routes |

---

## MC04.5 sprint delta

| Category | Count |
|----------|------:|
| Feature code changes | **0** |
| Runtime changes | **0** |
| Documentation (MC04.5) | Attestation pack only |
