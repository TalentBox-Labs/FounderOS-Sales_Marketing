# Founder OS COS-ARCH-v1 Baseline Manifest

**STATUS:** ARCHITECTURE BASELINE (documentation)  
**Sprint:** COS-ARCH-v1  
**Branch:** `founder-os-architecture-v1`  
**Commit:** `a7463e5e6bb8785749c6f5faab972e75dccc6b5f`  
**Tag:** `founder-os-demo-runtime-v1.0`

This manifest does **not** freeze runtime. It inventories the architecture pack and the **binding** frozen evidence it sits on.

---

## 1. Pack files

All under `docs/founder_os/commercial_architecture/v1/`:

1. `FOUNDER_OS_COMMERCIAL_OS_MASTER_ARCHITECTURE_v1.md`  
2. `FOUNDER_OS_PRODUCT_HIERARCHY_v1.md`  
3. `FOUNDER_OS_COMMERCIAL_GRAPH_v1.md`  
4. `FOUNDER_OS_DOMAIN_OWNERSHIP_MATRIX_v1.md`  
5. `FOUNDER_OS_COMMERCIAL_EVENT_CONTRACT_v1.md`  
6. `FOUNDER_OS_FOUNDER_PROFILE_CONTEXT_v1.md`  
7. `FOUNDER_OS_EXPERIENCE_ARCHITECTURE_v1.md`  
8. `FOUNDER_OS_BACKEND_EXPERIENCE_CONTRACT_v1.md`  
9. `FOUNDER_OS_INTERNATIONAL_UI_REQUIREMENTS_v1.md`  
10. `FOUNDER_OS_COS1_VERTICAL_SLICE_v1.md`  
11. `FOUNDER_OS_CONTROLLED_PARALLELISM_MODEL_v1.md`  
12. `FOUNDER_OS_ARCHITECTURE_CONFLICT_AUDIT_v1.md`  
13. `FOUNDER_OS_COS_ROADMAP_v1.md`  
14. `FOUNDER_OS_COS_ARCH_BASELINE_MANIFEST_v1.md` (this file)

---

## 2. Binding frozen evidence (not rewritten)

| Area | Pointers |
|------|----------|
| Founder architecture law | `docs/architecture/Architecture_v2.2.md`, ADR-003/004/005/007 |
| Sales | `docs/sales/SALES_OS_ARCHITECTURE_BASELINE_v1.0.md`, domain/agent/marketing/revenue contracts |
| Marketing | `docs/architecture/Marketing_OS_v2.2.md` |
| Revenue orch | `docs/revenue/orchestration/m0_5` … `m4_5` baselines |
| Founder UI | `docs/ui/d1_5/*`, `docs/ui/d2/*` |
| Identity/tenant | `docs/saas/s1` … `s4` |
| UI1/UI2 cockpit | `docs/ui/ui2_5/*` (legacy attention) |

---

## 3. Implementation inventory (grounding)

| Layer | Path |
|-------|------|
| Models | `revenue_os/models/*.py` |
| Services | `revenue_os/services/*.py` |
| Orchestrator | `revenue_os/agents/orchestration.py` |
| Approvals | `revenue_os/models/approvals.py`, `revenue_os/services/approvals.py` |
| Provenance | `AgentActionLog`, `Activity` |
| UI routes | `runner_api_routers/ui.py` |
| Founder templates | `templates/founder_*.html`, `base.html` |
| Authority tests | `tests/test_saas_s*`, `tests/test_rev_orch_m*`, `tests/test_ui_d2_*` |

---

## 4. Explicit non-goals of this sprint

- No production code, templates, migrations, models  
- No framework migration  
- No test modifications  
- No COS-1 implementation  
- No commit/merge in sprint instructions  

---

## 5. Frontend direction

**HYBRID** — evolve Jinja Founder shell; do not migrate to SPA for COS.

---

## 6. COS-1 (next, not now)

Existing governed person journey (QD → contact → M1–M4 → approvals → outcome), not greenfield ICP entities.
