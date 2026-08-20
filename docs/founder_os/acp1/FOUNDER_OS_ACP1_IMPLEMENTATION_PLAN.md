# Founder OS ACP-1 — Implementation Plan

**STATUS:** IMPLEMENTED (awaiting human freeze review)
**Branch:** `founder-os-agent-control-plane`
**Baseline:** `founder-os-cos5-v1.0` @ `de5d896b35133db581901734d72698b045db05d7`

## Purpose

Harden existing autonomous/self-wake commercial paths so future agents cannot violate tenant isolation, human authority, outbound/booking authority, or provenance — **without** expanding autonomy.

## Binding clarifications applied

1. Tenant enumeration: allowlist ∩ ACTIVE `Organization`, else ACTIVE `Organization` only. Never Contact rows as tenant activation.
2. Hermes Deal creation: PROHIBITED even with org.
3. `create_deal_from_contact` org stamp: ownership correctness only — not autonomous eligibility.

## Surfaces

| Action | Path |
|--------|------|
| CREATE | `revenue_os/services/acp1_autonomous_boundary.py` |
| MODIFY | `scheduler.py`, `hermes_planner.py`, `follow_up_eligibility.py`, `deal_automation_service.py`, `gmail_sync.py` |
| CREATE | `tests/test_founder_os_acp1_authority_tenant_hardening.py` |
| CREATE | `docs/founder_os/acp1/*` |

## Explicit non-goals

No AgentRun/Task/agent registry, no new SoT/models/migrations, no autonomous send/book, no agent self-approval, no generic multi-agent framework.
