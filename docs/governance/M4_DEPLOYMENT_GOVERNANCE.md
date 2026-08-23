# M4 — Deployment Governance (Ledger)

**Role:** Agent Ledger — Governance  
**Sprint:** M4 — Website Deployment Decision  
**Date:** 2026-08-10  
**Status:** GOVERNANCE ATTESTATION  
**Owned file:** this document only (`docs/governance/M4_DEPLOYMENT_GOVERNANCE.md`)  
**Code / API / DB / runtime / git application changes:** **NONE**

**Authoritative parents:**

| Source | Version / ID |
|--------|----------------|
| Architecture | v2.2 — [Architecture_ADR_003.md](../architecture/Architecture_ADR_003.md), [Architecture_v2.2.md](../architecture/Architecture_v2.2.md) |
| Platform agents | [PLATFORM_AGENT_REGISTRY.md](PLATFORM_AGENT_REGISTRY.md) v1.0 |
| Execution | [MULTI_AGENT_EXECUTION_STANDARD.md](MULTI_AGENT_EXECUTION_STANDARD.md) v1.0 |
| Ownership | [AGENT_OWNERSHIP_MATRIX.md](AGENT_OWNERSHIP_MATRIX.md) v1.0 |

**Sprint evidence (read-only):**

| Agent | Artifact |
|-------|----------|
| Nova | [M4_NOVA_DEPLOYMENT_REQUIREMENTS.md](../marketing/M4_NOVA_DEPLOYMENT_REQUIREMENTS.md) |
| Hermes | [M4_HERMES_PUBLISHING_COMPATIBILITY.md](../marketing/M4_HERMES_PUBLISHING_COMPATIBILITY.md) |
| Scout | [M4_SCOUT_DEPLOYMENT_COMPARISON.md](../marketing/M4_SCOUT_DEPLOYMENT_COMPARISON.md) |
| Sentinel | [M4_SENTINEL_REGRESSION.md](../marketing/M4_SENTINEL_REGRESSION.md) |
| Atlas | [M4_ATLAS_ARCHITECTURE_VALIDATION.md](../marketing/M4_ATLAS_ARCHITECTURE_VALIDATION.md) |
| Coordinator | [M4_DEPLOYMENT_DECISION.md](../marketing/M4_DEPLOYMENT_DECISION.md), [M4_DEPLOYMENT_ARCHITECTURE.md](../marketing/M4_DEPLOYMENT_ARCHITECTURE.md), [M4_EXECUTION_SUMMARY.md](../marketing/M4_EXECUTION_SUMMARY.md) |

---

## 1. Mission

Certify that the M4 Website deployment-mode decision sprint complies with Architecture ADR-003 / v2.2, Platform Agent Registry v1.0, Multi-Agent Execution Standard, and Agent Ownership Matrix — and that **production publish / deploy remain human gates** (agents recommend only).

---

## 2. Compliance matrix

| Standard | Check | Result |
|----------|-------|--------|
| **ADR-003 / Architecture v2.2** | Publishing orchestration ≠ Website render; Website Engine owns site publish + future deploy hooks; Static first / CMS later; M4 = deploy-mode decision (not Core expansion) | **PASS** |
| **Registry — Nova** | Website Engine requirements / artifact path / Core≠deploy hooks | **PASS** (owned file only; recommend / analysis) |
| **Registry — Hermes** | Publishing remains orchestration-only; no deploy/hosting in Publishing | **PASS** |
| **Registry — Atlas** | Architecture validation; provider independence; layer model | **PASS** |
| **Registry — Scout** | Research comparison; recommend-only mode ranking | **PASS** |
| **Registry — Sentinel** | Regression attest; 0 new regressions; docs-only sprint | **PASS** |
| **Registry — Ledger** | This governance attestation under `docs/governance/**` | **PASS** (this file) |
| **Ownership Matrix** | Non-overlapping write sets; Hermes ↔ Nova conflict avoided (docs separated; no code) | **PASS** |
| **Execution Standard** | Owned-file lists; no concurrent same-file writes; frozen baselines not silently expanded; no paid tools / secrets / architecture redesign | **PASS** |
| **Execution Standard §8** | Agents recommend; humans approve at mandatory gates; Founder required for M4 public deployment mode selection | **PASS** (see §4 — Founder Accept still open) |

**Conflicts recorded by Coordinator:** **0**

**Application code changes in M4:** **0**

---

## 3. Architecture boundary attestation (v2.2)

| Boundary | Sprint posture | Status |
|----------|----------------|--------|
| Website Engine owns website publish destination + future deploy hooks | Affirmed (Nova / Atlas / decision architecture) | **PASS** |
| Publishing Engine = orchestration only | Hermes PASS; website channel PLACEHOLDER retained | **PASS** |
| Deploy outside Website Engine Core / Static Provider v1.0 | Hooks = M5 layer; Core/Static frozen | **PASS** |
| CMS (WordPress/Ghost) deferred | Deferred in decision + Atlas | **PASS** |
| SEO / Social / Campaign ≠ site deploy | Unchanged / forbidden | **PASS** |
| Automation = transport; Shared = secrets | Affirmed for future M5 | **PASS** |

Atlas: **Architecture PASS · Provider Independence PASS**  
Sentinel: **Regression PASS · New Regressions 0**

---

## 4. Human gates (binding)

Architecture v2.2 mandatory human gates and Marketing OS production-publishing gate remain in force. Platform Agent Registry and Execution Standard require **Founder (or designated human)** for **M4 public deployment mode selection** and for **production site publish / deploy attestation**.

| Gate | Who may act | Agent role | Status |
|------|-------------|------------|--------|
| Editorial approval | Human | Agents do not approve | **Unchanged / required** |
| Production publishing | Human (Publishing + channel engines) | Hermes / Nova recommend only; no auto-publish | **Unchanged / required** |
| Production public website deploy / exposure | Human (Website Engine + Founder) | Agents recommend only; auto-deploy on approval **forbidden** | **Unchanged / required** |
| **M4 public deployment mode selection** | **Founder** (Execution Standard §8; Nova registry) | Scout/Coordinator package a recommendation | **OPEN — Founder Accept not evidenced** |
| Brand / Campaign / Revenue / customer-facing AI policy | Human | Out of M4 scope | N/A |

### Agents recommend only — attestation

| Agent | Language in owned artifact | Compliant? |
|-------|----------------------------|------------|
| Scout | **Recommended Mode:** Static self-host | **YES** |
| Nova | Requirements + recommended artifact path; explicit non-decisions | **YES** |
| Hermes | Compatibility PASS + M5 constraints; no mode selection as Founder Accept | **YES** |
| Atlas | Validates constraints; explicitly does **not** choose mode A/B/C | **YES** |
| Sentinel | Regression only | **YES** |
| Ledger | Certifies process; does **not** ratify Founder gates | **YES** |

### Coordinator packaging note (non-blocking wording hygiene)

[M4_DEPLOYMENT_DECISION.md](../marketing/M4_DEPLOYMENT_DECISION.md) and [M4_DEPLOYMENT_ARCHITECTURE.md](../marketing/M4_DEPLOYMENT_ARCHITECTURE.md) use status **DECIDED**. Under Execution Standard §8, that Coordinator packaging is treated by Ledger as:

> **Recommended canonical mode: Static self-host — pending Founder Accept.**

It is **not** Founder ratification. [M4_EXECUTION_SUMMARY.md](../marketing/M4_EXECUTION_SUMMARY.md) correctly labels **Deployment Recommendation**.

**M5 implementation** may proceed only as prep under the recommended mode **after** Founder Accept of the mode (or written Founder override). Production publish/deploy remain separately gated and human-attested.

---

## 5. Recommended mode (agent packet — not Founder Accept)

| Field | Value |
|-------|-------|
| Recommended mode | **Static self-host** |
| Secondary | Git-based hosting (same public artifact tree) |
| Deferred | Managed static; container; CMS adapters |
| Paid infrastructure required? | **NO** (not technically required) |
| Founder Accept recorded in repo? | **NO** |

---

## 6. Minor findings (non-failing)

1. Scout header cites Architecture **v2.1**; Atlas / Coordinator / decision docs cite **v2.2**. Substance aligns with v2.2 Website/Publishing split; non-blocking for research role.  
2. Coordinator “DECIDED” / “READY FOR M5” language risks overstating Founder authority — remapped in §4; does not fail agent ownership or architecture boundaries.

---

## 7. Impact

| Dimension | Impact |
|-----------|--------|
| Architecture runtime | **NONE** |
| Code / API / DB | **NONE** |
| Runtime / deploy | **NONE** (M4 docs-only) |

---

## FINAL

```text
Governance: PASS

Key compliance bullets:
1. ADR-003 / Architecture v2.2: Website owns deploy hooks; Publishing stays orchestration-only; Core/Static frozen; CMS deferred — Atlas PASS.
2. Registry v1.0 ownership honored: Nova (Website), Hermes (Publishing), Atlas (architecture), Scout (research), Sentinel (regression), Ledger (this file); write sets non-overlapping; code changes 0.
3. MULTI_AGENT_EXECUTION_STANDARD + Ownership Matrix: owned-file discipline, 0 conflicts, frozen baselines not expanded, no paid-tool/secret commits.
4. Human gates confirmed: production publish and production deploy remain human-approved; agents recommend only; auto-deploy forbidden.
5. Founder Accept for M4 public deployment mode selection remains OPEN — Coordinator “DECIDED” = recommended Static self-host pending Founder ratification (Execution Standard §8).
```
