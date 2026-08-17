# OF1 — Implementation Manifest

**Sprint:** FOUNDER OS OF1  
**Date:** 2026-08-13

| File | Class | Purpose | Runtime behavior | Frozen contract | DB | Security | Stage |
|------|-------|---------|------------------|-----------------|----|----------|-------|
| `revenue_os/services/operator_flow_read_model.py` | NEW | Read composition | Read-only snapshot | NO | NO | None | All (read) |
| `runner_api_routers/operator_flow.py` | NEW | Trusted action proxies | New `/api/v1/operator/*` | NO | NO | Trusted operator | All mutations |
| `templates/operator.html` | NEW | Operator UI | New `/operator` HTML | NO | NO | Buttons gated on operator | All |
| `runner_api_routers/ui.py` | MODIFIED | `GET /operator` | New page route | NO | NO | None | Shell |
| `runner_api.py` | MODIFIED | Mount router | New API prefix | NO | NO | Same API key | Shell |
| `templates/base.html` | MODIFIED | Nav link | Nav only | NO | NO | None | Nav |
| `templates/cockpit.html` | MODIFIED | Deep-link | Link only; no new mutation | NO (UI2.5 allowed nav) | NO | None | Cockpit link |
| `tests/test_of1_operator_flow.py` | NEW | Focused tests | Test only | NO | NO | Covers gates | Tests |
| `docs/operator/of1/*` | NEW | Docs | None | NO | NO | — | Docs |
