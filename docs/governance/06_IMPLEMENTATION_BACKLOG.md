# 06 — Implementation Backlog

Sprint P0 — Documentation only  
Date: 2026-08-09

Effort: **S** ≤1 day · **M** 2–5 days · **L** 1–2 weeks · **XL** >2 weeks

---

## P0 — Critical path / blockers

| Title | Description | Dependencies | Risk | Expected outcome | Effort |
|-------|-------------|--------------|------|------------------|--------|
| Complete Founder Decision Record | Fill FDR-001/002/003 in F0 record | F0 packet | LOW (governance) | E7 unblocked | S |
| Accept Editorial Approval ADR | Amend ADR PROPOSED→Accepted per FDR | FDR complete | LOW | Canonical approval semantics | S |
| E7 Approval Command | Thin HTTP/CLI surface over `promote_staged` + audit; no publish | FDR; Readiness freeze | MEDIUM | Editorial approve path | M |
| Protect frozen CS / Kanban / Readiness | No contract drift in parallel work | Baselines | MEDIUM | Regressions avoided | S (ongoing) |

---

## P1 — Near-term platform & marketing

| Title | Description | Dependencies | Risk | Expected outcome | Effort |
|-------|-------------|--------------|------|------------------|--------|
| Ruff tooling PR | Add Ruff per Toolchain v1.0 ADD NOW; confirm OSS | Toolchain freeze | LOW | Lint gate | S–M |
| CrewAI pin hygiene | Align requirements pin conflict GAP-007 | AI Runtime | MEDIUM | Reproducible installs | S |
| Editorial readiness UI link | Optional read-only surface on CS detail | Readiness API | LOW | Operator visibility | S |
| Fix `/edit` `/generate` staging args | Wire staging flags (follow-up; higher blast than E7) | Pipeline router | HIGH | HTTP generate/edit usable | M |
| Publishing boundary tests | Assert approve≠publish per FDR-003 | E7 | LOW | Guardrails | S |

---

## P2 — Sales / revenue / quality

| Title | Description | Dependencies | Risk | Expected outcome | Effort |
|-------|-------------|--------------|------|------------------|--------|
| Sales router hardening + tests | Prospecting/outreach stability | CRM/Auth | MEDIUM | Fewer sales regressions | M |
| CRM SPA reliability | Against frozen auth patterns | frontend/, crm router | MEDIUM | Usable CRM | M |
| pip-audit CI gate | Per toolchain ADD LATER gate | Pin hygiene | LOW | CVE visibility | S |
| Historical 8-test leave-behinds | Reclassify or fix stale unit contracts | Test owners | MEDIUM | Cleaner CI signal | M |
| Content quality in default pipeline | Optional; wire 2c carefully | Editorial | MEDIUM | Stronger gates | M |

---

## P3 — Later phases

| Title | Description | Dependencies | Risk | Expected outcome | Effort |
|-------|-------------|--------------|------|------------------|--------|
| Reject / revoke editorial decisions | After FD-6/FD-7 | E7 | MEDIUM | Full approval lifecycle | M–L |
| Lifecycle ADR + tracker Approved state | Only if FDR/FD-4 chooses | Lifecycle ADR | HIGH | Status semantics | L |
| Calendar read-only | After date SoT ADR (E5A blocked) | Date fields | HIGH | Calendar UI | L |
| Publishing Engine sprint | Hashnode/go-live hardening | FDR-003 | HIGH | Safer publish | M–L |
| Campaigns engine | After publishing | Marketing | HIGH | Campaign ops | XL |
| Automation reliability | Celery/n8n loops | Redis | MEDIUM | Durable jobs | M–L |
| Knowledge Base / RAG hardening | Chroma keep/retire | AI Runtime | MEDIUM | Usable KB | M–L |
| Analytics depth | Reporting | Revenue data | MEDIUM | Insights | M |
| Playwright E2E | Per toolchain gate | Mutation UI | MEDIUM | Browser coverage | M |
| Prometheus + Grafana | Per toolchain gate | Prod multi-instance | MEDIUM | SLO monitoring | M |

---

## Explicitly not backlog (until unblocked)

| Item | Why |
|------|-----|
| CMS OpenClaw/Sheets as SoT | Rejected |
| LangChain replace CrewAI | Rejected without AI ADR |
| Paid APM / Zapier | Toolchain reject / Founder paid approval |
| Architecture redesign | Frozen |
