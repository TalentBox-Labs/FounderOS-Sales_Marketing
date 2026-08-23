# Founder OS ACP-3 — Regression Reconciliation

## Focused

`tests/test_founder_os_acp3_durable_runtime.py` — **18/18 passed**

## Core regression (executed)

ACP-3 + ACP-2 + ACP-1 + COS-5/4/3 + tenant remediation + COS-2/1 + MC04 v2 + UI-D2 + S3 + S3.5

**Result: 254 passed**

Command (local):

```bash
SECRET_KEY=ui-d2-1-local-test-secret-key-32b python -m pytest \
  tests/test_founder_os_acp3_durable_runtime.py \
  tests/test_founder_os_acp2_agent_orchestration.py \
  tests/test_founder_os_acp1_authority_tenant_hardening.py \
  tests/test_founder_os_cos5_command_operating_surface.py \
  tests/test_founder_os_cos4_commercial_funnel_intelligence.py \
  tests/test_founder_os_cos3_commercial_decision_loop.py \
  tests/test_founder_os_tenant_remediation_v1.py \
  tests/test_founder_os_cos2_marketing_qualified_demand.py \
  tests/test_founder_os_cos1_commercial_spine.py \
  tests/test_mc04_qualified_demand_tenant_v2.py \
  tests/test_ui_d2_backward_compatibility.py \
  tests/test_ui_d2_live_governed_booking.py \
  tests/test_saas_s3_crm_tenant_isolation.py \
  tests/test_saas_s3_5_crm_tenant_isolation_baseline_freeze.py \
  -q
```

## Frozen tests modified

**0**

## Pre-existing residuals (not ACP-3)

UI-D1.5 `decision_loop` template drift and S2.5 `503→403` remain pre-existing on prior baselines (documented in ACP-1/ACP-2). Not re-run as pass criteria for ACP-3 freeze; do not rewrite frozen tests.
