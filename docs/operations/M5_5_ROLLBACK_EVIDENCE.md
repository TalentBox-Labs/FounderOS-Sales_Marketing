# M5.5 — Rollback Evidence (Local)

**Agent:** Ledger  
**Sprint:** M5.5  
**Date:** 2026-08-10  
**External deployment:** **NONE**

---

## Procedure executed

1. **Package A** — Publish Static artifacts with HTML marker `M55_PACKAGE_A_MARKER`; `export_package(deployment_id=dep_m55_pkg_a)`.  
2. **Deploy A** — `deploy_local(docroot, deployment_id=dep_m55_pkg_a, export_first=False)`.  
3. **Package B** — Re-publish source with `M55_PACKAGE_B_MARKER`; `export_package(deployment_id=dep_m55_pkg_b)`.  
4. **Deploy B** — `deploy_local(docroot, deployment_id=dep_m55_pkg_b, export_first=False)`.  
5. **Rollback** — `deploy_local(docroot, deployment_id=dep_m55_pkg_a, export_first=False)`.  
6. **Verify** — Docroot HTML contains A marker, not B marker.  
7. **Integrity** — Manifest SHA-256 entries match package A files on disk.  
8. **Exclusion** — Package A has no `metadata.json` / `source.md`; source tree still has operator files.

---

## Result

| Check | Outcome |
|-------|---------|
| Package A deployed | **PASS** |
| Snapshot created | **PASS** (`snapshots/dep_m55_pkg_a/`) |
| Package B overwrote docroot | **PASS** |
| Rollback restored A | **PASS** |
| Manifest checksums | **PASS** (3 public files + manifest excluded from hash list) |
| Operator artifacts excluded from package | **PASS** |

**Smoke stdout:**

```json
{
  "package_a": "dep_m55_pkg_a",
  "package_b": "dep_m55_pkg_b",
  "rollback_ok": true,
  "manifest_files": 3,
  "operator_excluded": true
}
```

**Exit code:** `0` (`SMOKE_OK`)

---

## Rollback mechanism (frozen)

| Layer | Action |
|-------|--------|
| Local docroot | Re-run `deploy_local` with prior `deployment_id` |
| Snapshot | `output/website-deploy/snapshots/{deployment_id}/` |
| History | `rollback-history.jsonl` append records |
| Cloudflare (future) | Dashboard production rollback — not exercised in M5.5 |

---

## Verdict

**Rollback: PASS** (local, reproducible, no external host)
