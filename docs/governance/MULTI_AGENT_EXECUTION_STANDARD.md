# Multi-Agent Execution Standard v1.0

**Status:** READY (governance)  
**Sprint:** G2  
**Date:** 2026-08-10  
**Parent:** [PLATFORM_AGENT_REGISTRY.md](PLATFORM_AGENT_REGISTRY.md)  
**Architecture:** v2.2

Governance only. No runtime agent framework changes in G2.

---

## 1. Purpose

Standardize how Founder OS **platform agents** (Atlas, Forge, Sentinel, Ledger, Beacon, Hermes, Nova, Pulse, Scout, Cipher) coordinate on multi-agent sprints without file collisions, boundary violations, or silent gate bypasses.

---

## 2. Execution Rules

1. **Architecture v2.2 is authoritative** for OS vs Platform ownership.  
2. **Registry v1.0 is authoritative** for agent missions and file zones.  
3. **No concurrent writes** to the same file by two agents.  
4. **Owned-file lists** must be declared before edits.  
5. **Agents recommend; humans approve** at mandatory gates.  
6. **Automation executes** only after approval when required — agents do not become Automation Platform.  
7. **Frozen baselines** (Publishing, Website, Editorial, Architecture) cannot be silently expanded.  
8. **No paid tools / no secret commits / no git network ops** unless the human sprint brief explicitly allows.  
9. **No architecture redesign** inside implementation sprints unless Atlas is assigned and Founder approves.  
10. **Sentinel never relabels new failures as historical** without naming test IDs.

---

## 3. Multi-agent coordination

### 3.1 Roles in a parallel sprint

| Role | Who | Duty |
|------|-----|------|
| **Coordinator** | Human Lead Engineering Coordinator (or designated agent acting as coordinator) | Assign ownership, launch agents, reconcile, reject conflicts, produce summary |
| **Implementer** | Forge / Hermes / Nova / Pulse / Scout (as assigned) | Edit owned files only |
| **Auditor** | Sentinel / Cipher / Atlas (as assigned) | Read-only + owned audit docs |
| **Scribe** | Ledger / Beacon | Freeze docs, registry, cross-links |

### 3.2 Parallelization pattern

```
Coordinator declares ownership blocks
        ↓
Launch non-overlapping agents in parallel
        ↓
Agents return structured finals
        ↓
Coordinator reconciles + optional Sentinel full suite
        ↓
Ledger/Beacon write summary / freeze
```

If ownership would overlap → **STOP** that modification → Coordinator reassigns.

---

## 4. Conflict resolution

| Conflict type | Resolution |
|---------------|------------|
| Same file claimed by two agents | Coordinator picks single owner; other agent documents-only or waits |
| Boundary dispute (e.g. Hermes vs Nova) | Atlas interprets Architecture; Ledger records |
| New regression vs historical | Sentinel lists IDs; Forge fixes if owned; no silent ignore |
| Frozen contract vs feature ask | Ledger blocks; requires new baseline/ADR |
| Security concern | Cipher veto until Founder waiver |
| Mandatory human gate | Human decision required; agents may only prepare packets |

**Reject conflicting edits:** Coordinator keeps the assigned owner’s version or reverts both and re-runs serially.

---

## 5. Coordinator responsibilities

1. Restate mission and Architecture parent.  
2. Publish **file ownership table** before launches.  
3. Launch agents with non-overlapping write sets.  
4. Collect structured finals (PASS/FAIL, counts).  
5. Detect conflicts; resolve or abort slice.  
6. Confirm M-engine work does not confuse internal UI with public Website.  
7. Request Sentinel regression when code changed.  
8. Produce parallel execution / freeze summary.  
9. Never claim READY if New Regressions > 0 without Founder waiver.

---

## 6. File ownership

- Declared per sprint in the Coordinator brief.  
- Default zones from [AGENT_OWNERSHIP_MATRIX.md](AGENT_OWNERSHIP_MATRIX.md).  
- Read-only access to foreign files is allowed for evidence.  
- Write to foreign files requires Coordinator reassignment.

---

## 7. Escalation matrix

| Severity | Trigger | Escalate to |
|----------|---------|-------------|
| L1 | Ambiguous test flake | Sentinel → Forge |
| L2 | File ownership conflict | Coordinator |
| L3 | OS/Platform boundary ambiguity | Atlas → Coordinator |
| L4 | Mandatory gate / FDR impact | Ledger → Founder |
| L5 | Secret leak / auth break | Cipher → Founder (immediate) |

---

## 8. Approval chain

```
Agent recommendation
    → Coordinator acceptance of sprint slice
        → Engine owner agent (Hermes/Nova/…) implementation
            → Sentinel regression attest
                → Ledger baseline / freeze (if certification sprint)
                    → Founder (when FDR / Architecture Accept / public deploy / auth change)
```

**Always Founder (or designated human) for:**

- Architecture version Accept  
- Editorial / Campaign / Production publish / Brand policy / Revenue-impacting automation / Customer-facing AI policy  
- Waiving new regressions  
- M4 public deployment mode selection  

---

## 9. Canonical agent control flow (Architecture-aligned)

```
Agent → Recommendation → Human Approval (when required)
  → Automation Platform → Execution → Audit
```

Platform agents in this registry participate as the “Agent / Recommendation / Audit-doc” layers. They do **not** replace Automation Platform or Shared Platform auth.

---

## 10. Impact (G2)

| Dimension | Impact |
|-----------|--------|
| Architecture runtime | NONE |
| Code | NONE |
| Runtime | NONE |
