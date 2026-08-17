# R1E — R1D Accounting Reconciliation

**Date:** 2026-08-12  
**Sprint:** R1E pre-flight  
**Question:** Confirmed(10) + Removed(4) + Deferred(5) appear to total 9 when summing Removed+Deferred — what happened to the “missing” confirmed item?

---

## Verdict

**R1D Accounting Reconciled: YES**

**Classification of the apparent gap:** **REPORTING ERROR** (category conflation), not a lost removal.

---

## Correct arithmetic

The R1D **15** dead-code candidates split into two **disjoint** sets:

| Set | Count | Members |
|-----|------:|---------|
| **Confirmed dead** | **10** | #1–#10 |
| **Deferred** | **5** | #11–#15 |
| **Total reviewed** | **15** | |

Confirmed dead were **all removed**, but across **two sprints**:

| Bucket | Count | Classification |
|--------|------:|----------------|
| Removed in **R1A** (before R1D) | **6** | **REMOVED FILE** (5× `*.py.old` + empty `revenue_os/pipeline/`) |
| Removed in **R1D** | **4** | **REMOVED FILE** ×3 + **REMOVED SYMBOL** ×1 (`_render_orchestration_run_detail`) |
| **Confirmed total** | **10** | |

Deferred (**5**) were **never** part of Confirmed(10).

### Why Removed(4)+Deferred(5)=9 looked wrong

That sum **incorrectly mixes** Deferred with Confirmed and **omits** the **6** R1A removals already counted inside Confirmed(10).

Correct identity:

```
Confirmed(10) = R1A REMOVED FILE(6) + R1D REMOVED FILE/SYMBOL(4)
Deferred(5)   = separate remaining candidates
15            = Confirmed(10) + Deferred(5)
```

### R1D “Dead Code Removed: 4” metric

Means **removals performed during R1D only**, not cumulative confirmed-dead removals.

The R1D symbol removal (`_render_orchestration_run_detail`) is **REMOVED SYMBOL**; the three scripts/modules are **REMOVED FILE**. Together they are the **4** R1D removals — not a missing 11th confirmed item.

---

## No outstanding confirmed-dead orphan

There is **no** unreconciled confirmed-dead artifact left undeleted from the R1D confirmed set.
