# M5 — Publishing ↔ Deployment Validation (Hermes)

**Agent:** Hermes — Publishing Engine  
**Sprint:** M5  
**Date:** 2026-08-10  
**Code changes to Publishing Engine:** **NONE**

---

## Verification

| Check | Result | Evidence |
|-------|--------|----------|
| Publishing remains orchestration-only | **PASS** | `publishing_engine.py` unchanged; `_adapter_website` still PLACEHOLDER |
| No deployment logic in Publishing | **PASS** | No imports of `website_deployment`; no deploy APIs |
| Website bundles produced by Website Engine | **PASS** | Static Provider writes `output/website/`; adapter reads same tree |
| Future handoff shape | **COMPATIBLE** | Operator or Automation calls `DeploymentAdapter` after publish; Publishing may record orchestration in `adapter_result` without owning deploy |

---

## Handoff model (M5)

```text
Publishing Engine (orchestration) ──optional future invoke──► Website Engine (render/static write)
                                                                      │
                                                                      ▼
                                                          output/website/
                                                                      │
                                                          DeploymentAdapter.export_package()
                                                                      │
                                                          Cloudflare Pages / local docroot
```

Publishing does **not** call the Deployment Adapter in M5. Bundle completion is satisfied when Static Provider artifacts exist on disk; deploy is a separate operator/Automation step.

---

## Verdict

**PASS** — Publishing Engine boundary preserved.
