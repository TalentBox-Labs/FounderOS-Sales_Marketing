# 04 — Parallel Development Guide

Sprint P0 — Documentation only  
Date: 2026-08-09

---

## Safe concurrent work

| Stream A | Stream B | Why safe |
|----------|----------|----------|
| Editorial E7 (after FDR) | Sales/CRM router tests | Separate domains |
| Ruff tooling PR | Content Studio read-only docs/UI polish | Tooling vs templates/API builders |
| Knowledge Base / Analytics read paths | Publishing docs/ADRs | Soft coupling |
| Migration/governance docs | Any code stream | Docs-only |

---

## Unsafe concurrent work

| Streams | Why unsafe |
|---------|------------|
| Two PRs both editing `runner_api.py` includes | Merge conflicts; router order |
| Auth redesign + any API feature | Frozen dual-auth; high blast |
| Content Studio API contract change + Kanban/UI | Frozen baselines |
| Editorial Approval + Publishing auto-wire | Violates FDR-003 / ADR until decided |
| Two CrewAI YAML/prompt edits + pipeline | Prompt/contract drift |
| Alembic migrations from two features | Schema race |

---

## Shared files (serialize or tiny PRs)

| File / area | Rule |
|-------------|------|
| `runner_api.py` | One owner PR at a time; additive includes only |
| `runner_api_routers/utils.py` | Coordinate; prefer no drive-by edits |
| `templates/base.html` | Nav changes only with UI owner |
| `requirements*.txt` | One dependency PR at a time |
| `.pre-commit-config.yaml` / CI workflow | Tooling owner only |
| `tracker.csv` / `input/` | Not feature SoT for random edits |

---

## Protected modules (frozen — no redesign)

| Module | Protection |
|--------|------------|
| Architecture Baseline | No new domains / topology redesign |
| Content Studio read API contract | Additive only |
| Kanban / Editorial Readiness | No mutation semantics |
| Toolchain Baseline v1.0 | Gates + governance rule |
| Calendar | Blocked (E5A ADR) |
| Approval ADR | No implement until FDR filled |

---

## Branch strategy

| Pattern | Use |
|---------|-----|
| `develop` | Integration branch (current canonical) |
| `feat/<module>-<short>` | One feature / one sprint outcome |
| `chore/ruff` / `chore/deps` | Tooling only |
| `docs/<topic>` | Governance/migration docs |

Avoid long-lived multi-feature branches.

---

## Merge strategy

1. Rebase or merge `develop` frequently.  
2. Prefer small PRs (<~400 LOC code when possible).  
3. Docs-only PRs may merge independently.  
4. Never `--force` to main/develop without explicit Founder/ops request.

---

## Conflict strategy

1. Shared file conflict → module owner wins API/contract; feature author re-applies.  
2. Frozen contract conflict → revert to frozen behavior; open ADR if change required.  
3. Dual approval systems (Revenue vs Editorial) → keep separate; do not “unify” in merge.

---

## Review strategy

| Change type | Required checks |
|-------------|-----------------|
| Feature | Focused tests + relevant regression + DoD |
| Tooling (Ruff) | License note + no app behavior change |
| Editorial mutation | FDR satisfied + read-only guarantees preserved elsewhere |
| Auth / DB / Compose | Extra scrutiny; prefer defer |

---

## When multiple developers can work simultaneously

Yes, when each owns a **different module row** from [01_MODULE_OWNERSHIP.md](01_MODULE_OWNERSHIP.md) and avoids **shared files** list.  
Serialize work on Platform shell (`runner_api.py`), Auth, and frozen Content Studio contracts.
