# M7.5 — Publishing Path Certification (Hermes)

**Agent:** Hermes  
**Sprint:** M7.5  
**Date:** 2026-08-10  
**New production article created:** **NO**

---

## Certified chain (as implemented)

```text
Content Studio (read / Kanban — Marketing OS)
        ↓
Editorial Engine (readiness + human approve/reject)
        ↓
Publishing Engine v1.0 (orchestration; website channel PLACEHOLDER)
        ↓
Website Engine Core v1.0 (render / metadata / feeds — when invoked / operator publish)
        ↓
Static Provider v1.0 → output/website/
        ↓
Deployment Adapter v1.0 → public subset / Direct Upload
        ↓
Cloudflare Pages (Production / main)
        ↓
https://founderos-staging.pages.dev
```

---

## Boundary evidence

| Boundary | Evidence |
|----------|----------|
| Editorial human gate | Editorial approval module + UI/API (E7); approval ≠ publish |
| Publishing orchestration-only | `publishing_engine.py` — website PLACEHOLDER; no deploy ownership |
| Website / Static | Frozen Core + Static Provider; RC1 artifacts |
| Deployment Adapter | `website_deployment` — outside Core |
| Cloudflare | External host; production deploy ID `80d03643…` |
| Auditability | Publishing audit JSONL contract; deploy manifests/snapshots; M7 release docs |

**Publishing: PASS** (implemented staging→production path using approved RC1; no engine code changes in M7/M7.5)
