# 07 — Repository Status

Governance freeze for Migration Baseline v1.0.

---

## Canonical repository

| Field | Value |
|-------|-------|
| **Repository** | FounderOS-Sales_Marketing |
| **Local path** | `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing` |
| **Status** | **ACTIVE** |
| **Purpose** | Canonical engineering repository for Founder OS |
| **Branch (baseline)** | `develop` |
| **HEAD (baseline)** | `e1efc0892ea13dad856b952110c7cc38d24565c3` |

All product development, Content Studio Phase 2, and subsequent engine migrations must occur here.

---

## Reference repository

| Field | Value |
|-------|-------|
| **Repository** | workcrew-cms-os |
| **Local path** | `/Users/krishna/Documents/workcrew-cms-os` |
| **Status** | **REFERENCE ONLY** |
| **Purpose** | Migration evidence repository (UX patterns, content packs, historical dashboard) |

### Rules

- No new feature development in `workcrew-cms-os`.
- No Flask/Sheets/n8n runtime import into Founder as product SoT.
- Patterns may be adapted into Founder per approved slices ([03_MIGRATION_SLICES.md](../03_MIGRATION_SLICES.md)).

---

## Documentation capability pack

| Field | Value |
|-------|-------|
| **Pack** | CMS_OS_V1 |
| **Local path** | `/Users/krishna/Documents/CMS_OS_V1` |
| **Status** | REFERENCE ONLY (docs; 0 `.py`) |
| **Purpose** | Capability documentation corroboration ([01_CAPABILITY_MATRIX.md](../01_CAPABILITY_MATRIX.md)) |

---

## Governance statement

Future development must occur only in **FounderOS-Sales_Marketing**.

CMS and CMS_OS_V1 remain evidence/reference until formal archive (see [08_NEXT_PHASE.md](08_NEXT_PHASE.md)).
