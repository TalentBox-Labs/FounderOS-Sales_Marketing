# F0 — Founder Decision Review Packet

Sprint F0 — Governance only  
Date: 2026-08-09  
Code changes: **0**

Sources: [E6D_IMPLEMENTATION_DECISION_MATRIX.md](E6D_IMPLEMENTATION_DECISION_MATRIX.md), [ADR_EDITORIAL_APPROVAL_SEMANTICS.md](../architecture/adr/ADR_EDITORIAL_APPROVAL_SEMANTICS.md), [E6C_FOUNDER_DECISIONS.md](../migration/editorial-engine/E6C_FOUNDER_DECISIONS.md)

**This packet does not select options.** Founder completes [F0_FOUNDER_DECISION_RECORD.md](F0_FOUNDER_DECISION_RECORD.md).

---

# Executive Summary

E6D established **eight** Founder decisions and **three** that must be resolved before Sprint E7:

| Packet ID | E6C/E6D ID | E6D bucket | Role before E7 |
|-----------|------------|------------|----------------|
| **FDR-001** | FD-1 | BLOCKER | Approval object |
| **FDR-002** | FD-2 | BLOCKER | Approver identity / AI boundary |
| **FDR-003** | FD-5 | IMPLEMENTATION | Publishing authorization boundary |

E6D RELEASE item **FD-8** (audit field expansion) is **not** in this packet; it remains deferred until production hardening (E6D).

E7 target (evidence-aligned): thin Approval Command over existing `promote_staged` + `promotion_audit`. No code in F0.

---

# Decisions Required Before E7

---

## FDR-001

**E6C ID:** FD-1  
**E6D bucket:** BLOCKER

### Question

For Sprint E7 Editorial Approval, what is the approved object: a **phase-scoped staged artifact bundle** (2A / 2B / 3), a **single content-item approval** spanning the week, or **both**?

### Why Now

E7 cannot define request/response shape, persistence, or tests until the object is fixed. Content-item overlay implies Lifecycle ADR and new SoT before coding (E6D).

### Verified Evidence

| Kind | Detail |
|------|--------|
| File/module | `src/tools/promote_staged.py`, `src/tools/promotion_audit.py` |
| Current behavior | Promote copies phase-specific files into `input/{week}/` (2A: 01–04; 2B: 05_Final; 3: 06–09) |
| Existing constraint | No content-row “approval” entity in tracker or DB for Marketing content |
| Existing ADR finding | Interim: phase-scoped staged artifact bundle ([ADR_EDITORIAL_APPROVAL_SEMANTICS.md](../architecture/adr/ADR_EDITORIAL_APPROVAL_SEMANTICS.md)) |
| Runtime implication | FS copy + audit JSON/JSONL; no tracker status mutation on promote |

### Unresolved Policy

Whether a content-item approval overlay is required for product semantics; whether frontmatter `publish_status` values count as Editorial Approval.

### Available Options

#### Option A — Phase-scoped promote only

| Dimension | Consequence |
|-----------|-------------|
| Description | E7 Approval Command attests the same phase bundles as CLI `promote_staged` |
| Implementation | Thin wrap/call of existing promote + audit |
| API | Payload: `content_id`/`week_id` + `phase` (+ approver per FDR-002) |
| Audit | Existing `promotion_audit` records remain SoT |
| Security | Same as today’s promote trust model (see FDR-002) |
| Migration | None beyond API surface |
| Extensibility | Content-item overlay can be added later (FD-1 B/C later) |

#### Option B — Content-item approval only

| Dimension | Consequence |
|-----------|-------------|
| Description | One approval covers the week/content item; not phase file sets as primary object |
| Implementation | New persistence model; promote may become side effect or separate |
| API | Content-level approve resource; phase promote not primary |
| Audit | New or extended audit beyond phase promote |
| Security | Depends on FDR-002 |
| Migration | High — no current content-approval SoT |
| Extensibility | Aligns with CMS-like “item approved” UX; **Lifecycle ADR likely required** |

#### Option C — Both phase promote and content-item overlay

| Dimension | Consequence |
|-----------|-------------|
| Description | Keep phase promote; add content-item approval record |
| Implementation | Two mechanisms; ordering/rules required |
| API | Dual endpoints or composite command |
| Audit | Dual trails |
| Security | Depends on FDR-002 |
| Migration | High |
| Extensibility | Maximum flexibility; highest complexity |

### Invalid Options

None ruled out by architecture for the object itself.  
**Not permitted as substitute:** treating Editorial Readiness `readiness_summary` / `validation_passed` as the approval object (E6B.5 / ADR: observational only).

### Engineering Impact

| Once decided | E7 can implement | Modules likely affected | DB | API | Architecture |
|--------------|------------------|-------------------------|----|-----|--------------|
| Option A | Approval Command over promote | `promote_staged`, `promotion_audit`, new editorial approve router (likely), tests | NONE expected | Additive POST (likely) | NO change required by evidence |
| Option B/C | Not E7-thin; Lifecycle ADR first | tracker/Content Studio/Kanban contracts likely | Possible | Larger | Possibly YES → out of E7 freeze posture |

### What Can Be Deferred

**DEFERRED SAFELY:** FD-3 (readiness prerequisite), FD-4 (tracker Approved state), FD-6 (reject), FD-7 (revoke), FD-8 (audit enrichment).

### Minimum Founder Decision Required

Founder must select **exactly one** of: Option A, Option B, or Option C.  
If B or C: acknowledge Lifecycle ADR may be required before E7 proceeds.

---

## FDR-002

**E6C ID:** FD-2  
**E6D bucket:** BLOCKER

### Question

Who may act as Editorial Approver for E7, and how is **AI / automation** prevented from serving as approver: **ops free-text name**, **Shared Platform authenticated user + role**, or **free-text plus explicit deny of automation keys**?

### Why Now

E7 HTTP/API design differs completely for free-text vs role auth. Exposing promote beyond CLI without an actor policy expands the trust boundary (E6D).

### Verified Evidence

| Kind | Detail |
|------|--------|
| File/module | `src/tools/promote_staged.py` (`--approver`, `WORKCREW_PROMOTION_APPROVER`) |
| Current behavior | Any non-empty string unblocks promote; no role ACL |
| Existing constraint | API key auth exists for many routes (`_verify_api_key`); not bound to promote CLI today |
| Existing ADR finding | Human free-text ALLOWED (executable); AI Editorial Approval authority **NOT ALLOWED** (governing intent); enforcement FOUNDER DECISION |
| Runtime implication | AI/crews may write **staging**; promote is the attested gate |

### Unresolved Policy

Whether E7 requires authenticated human identity; how automation API keys are denied from approving; whether env-based approver remains valid for CLI-only ops.

### Available Options

#### Option A — Free-text human name (ops trust)

| Dimension | Consequence |
|-----------|-------------|
| Description | E7 passes approver string through to promote/audit (status quo) |
| Implementation | Minimal; mirror CLI |
| API | `approver: string` in body or header |
| Audit | `approver` string as today |
| Security | Spoofable; relies on ops trust / network control |
| Migration | None |
| Extensibility | Can harden to B/C later |

#### Option B — Shared Platform authenticated user + role

| Dimension | Consequence |
|-----------|-------------|
| Description | Approver = authenticated principal with editorial-approve role |
| Implementation | Shared Platform auth integration; map identity into audit |
| API | Session/token; no free-text spoof as sole authority |
| Audit | Prefer durable user id (+ display name) |
| Security | Strongest of the three viable options |
| Migration | Auth product dependency; may block E7 if auth incomplete |
| Extensibility | Best for multi-user production |

#### Option C — Free-text + deny automation keys for approve

| Dimension | Consequence |
|-----------|-------------|
| Description | Keep human name string; policy/config blocks known automation API keys from Approval Command |
| Implementation | Policy layer on approve route; CLI may remain separate |
| API | Approve route checks caller key class |
| Audit | Free-text approver + caller key metadata if logged |
| Security | Reduces AI/automation approve via API; CLI env still a residual risk unless also constrained |
| Migration | Config/deny-list maintenance |
| Extensibility | Bridge toward B |

### Invalid Options

| Option | Status |
|--------|--------|
| AI agent / QACrew / system automation **as Editorial Approver** | **NOT PERMITTED BY CURRENT ARCHITECTURE** (ADR: AI Approval Authority = NOT ALLOWED) |
| Using Revenue OS `/api/v1/approvals` `decided_by` as Editorial Approver | **NOT PERMITTED** as Editorial Approval (different domain; ADR) |

### Engineering Impact

| Once decided | E7 can implement | Modules likely affected | DB | API | Architecture |
|--------------|------------------|-------------------------|----|-----|--------------|
| A | Approve command with string actor | editorial router, promote subprocess/env, tests | NONE | Additive | NO |
| B | Approve behind role auth | Shared Platform auth, editorial router, audit fields | Possibly none if auth external | Auth-coupled | NO if auth already platform-owned |
| C | Approve + key-class guard | editorial router, API key classification | NONE | Additive + policy | NO |

### What Can Be Deferred

**DEFERRED SAFELY:** FD-8 full audit enrichment (user id/correlation) unless Option B requires user id in audit now; FD-6/FD-7; multi-role matrices beyond one approve role.

### Minimum Founder Decision Required

Founder must select **exactly one** of: Option A, Option B, or Option C,  
**and** reaffirm that AI/automation is **not** an authorized Editorial Approver.

---

## FDR-003

**E6C ID:** FD-5  
**E6D bucket:** IMPLEMENTATION (required before E7 per E6D minimum set)

### Question

Does a successful Editorial Approval (promote attestation) **authorize Publishing Engine execution**, or is it **editorial-only** (publish/go-live remain separate human/publishing steps)?

### Why Now

E7 Approval Command must not accidentally trigger or imply publish. Publishing boundary must be Founder-affirmed before any approve→publish wiring (E6D).

### Verified Evidence

| Kind | Detail |
|------|--------|
| File/module | `promote_staged.py`; `publish_checklist_checker.py`; `go_live_helpers.py`; `hashnode_publish.py` |
| Current behavior | Promote copies into `input/` + audit; does not publish; checklist notes human sign-off still required; go-live/hashnode are separate |
| Existing constraint | No `ready_for_publish` field; readiness explicitly not publish permission |
| Existing ADR finding | Decision A interim: Editorial Approval does **not** authorize Publishing Engine |
| Runtime implication | Publish paths remain operator/Publishing Engine owned |

### Unresolved Policy

Whether approval is later a **necessary** precondition for publish (without being sufficient), or may ever auto-trigger publish.

### Available Options

#### Option A — Editorial-only (never authorizes publish)

| Dimension | Consequence |
|-----------|-------------|
| Description | Approval/promote never starts Publishing Engine |
| Implementation | E7 approve ends at promote + audit |
| API | No publish side effects on approve |
| Audit | Promote audit only |
| Security | Clear separation of duties |
| Migration | None |
| Extensibility | Publishing auth can be a later Publishing Engine ADR |

#### Option B — Necessary but not sufficient for publish

| Dimension | Consequence |
|-----------|-------------|
| Description | Publish flows may require prior Editorial Approval; still need separate publish authorization |
| Implementation | Publishing Engine checks for prior promote/audit; E7 still must not auto-publish |
| API | Publish APIs gain precondition checks (not E7 scope if deferred) |
| Audit | Cross-link publish to promote audit later |
| Security | Stronger gate before publish |
| Migration | Publishing Engine changes after E7 |
| Extensibility | Good long-term; **E7 must still not auto-publish** |

#### Option C — Approval alone may trigger publish automation

| Dimension | Consequence |
|-----------|-------------|
| Description | Successful approve invokes publish path |
| Implementation | Couples Editorial Engine to Publishing Engine in E7+ |
| API | Approve becomes dual-purpose |
| Audit | Must record publish attempts from approve |
| Security | High blast; collapses separation of duties |
| Migration | High |
| Extensibility | Conflicts with current ADR interim Decision A |

### Invalid Options

None fully invalid, but **Option C contradicts ADR interim Decision A** and E6A/E6B publishing separation. Present as Founder override only if Founder explicitly rejects ADR Decision A.

Treating tracker `QA Passed` or readiness `all_default_reports_pass` as publish authorization: **NOT PERMITTED BY CURRENT ARCHITECTURE** (ADR / E6B.5).

### Engineering Impact

| Once decided | E7 can implement | Modules likely affected | DB | API | Architecture |
|--------------|------------------|-------------------------|----|-----|--------------|
| A | Approve = promote + audit only | editorial approve path, tests forbidding publish side effects | NONE | Additive approve only | NO |
| B | Same as A for E7; publish checks later | Future Publishing Engine | NONE for E7 | Later | NO for E7 |
| C | Out of thin E7; architecture coupling | promote + hashnode/go-live | Possible | Breaking boundary | Likely YES — not current evidence posture |

### What Can Be Deferred

**DEFERRED SAFELY:** Exact Publishing Engine precondition checks (if B); campaign/automation; FD-8; Calendar (E5A).

### Minimum Founder Decision Required

Founder must select **exactly one** of: Option A, Option B, or Option C.  
For E7 thin Approval Command, A or B both allow engineering to proceed **without** publish side effects in E7; C expands scope beyond current frozen architecture posture.

---

# E7 Dependency Summary

```
FDR-001 (object) ──┐
FDR-002 (actor)  ──┼──► E7 Approval Command design freeze
FDR-003 (publish)──┘         │
                             ▼
                    promote_staged + promotion_audit
                             │
                             ▼
                    (Publishing Engine only if FDR-003 = C;
                     otherwise separate, later)
```

| Deferred (not blocking E7) | IDs |
|----------------------------|-----|
| Readiness/QA mandatory couple | FD-3 |
| Tracker Approved lifecycle | FD-4 |
| Rejection | FD-6 |
| Revocation | FD-7 |
| Audit field expansion | FD-8 |

---

# Architecture Impact

**NO ARCHITECTURAL CHANGE REQUIRED BY CURRENT EVIDENCE**

for E7 under FDR-001 Option A + FDR-003 Option A or B + any FDR-002 option that does not invent a new domain.

FDR-001 Option B/C or FDR-003 Option C may force Lifecycle / Publishing architecture work **outside** the current no-change posture.
