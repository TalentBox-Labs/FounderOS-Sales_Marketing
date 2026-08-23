# OF1 — Architecture

**Sprint:** FOUNDER OS OF1  
**Date:** 2026-08-13

```
GET /operator  (Jinja Founder OS shell)
        ↓
build_operator_flow_snapshot()   # non-persistent read composition
        ↓
POST /api/v1/operator/actions/*  # trusted FOUNDER_OS_OPERATOR_NAME
        ↓
frozen services only:
  accept/reject_qualified_demand
  apply_contact_status_update
  apply_deal_stage_update
  register/accept/reject CommercialOutcome
  Deal ORM create (non-terminal) via existing pipeline helper
```

Cockpit remains observe/prioritize (UI2.5 two mutations unchanged).  
Operator Flow is inspect/decide/execute.
