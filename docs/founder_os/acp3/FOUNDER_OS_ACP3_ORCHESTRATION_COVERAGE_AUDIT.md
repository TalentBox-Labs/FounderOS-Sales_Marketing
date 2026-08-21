# Founder OS ACP-3 — Commercial Orchestration Coverage Audit

## Scheduler path classification

| Job | Class | Notes |
|-----|-------|-------|
| `score_new_leads` | **A** | ACP-2 unit orch + ACP-3 pause/kill gate |
| `scan_follow_up_eligibility` | **A** | Propose orch; send remains HUMAN_REQUIRED |
| `check_deals_at_risk` | **A** | ACP-3: per-deal WorkItem via `orchestrate` |
| `sync_gmail_inbox` | **A** | ACP-3: per-org WorkItem |
| `snapshot_pipeline_metrics` | **C** (+A provenance) | Observational; still orch + gates for coverage |
| `hermes_goal_check` | **Mixed** | Gate + org scope; Deal create **A/PROHIBITED**; score/qualify steps remain **B** (ACP-1 org-scoped, not every micro-step a WorkItem) |
| `acp3_reconcile` | **A** | Bounded reconcile/resume |
| Celery tasks | **E** | Dormant — **not activated** |

Legend: A=ACP-2 orchestrated · B=ACP-1 governed not unit-orch · C=observational · D=human-only · E=dormant

## Residual (documented, not accidental activation)

Hermes internal score/qualify recommendations may still run under ACP-1 tenant
scoping without per-step WorkItems. Deal creation path is orchestrated and
PROHIBITED. Full Hermes micro-step WorkItems are deferred (not required to claim
ACP-3 commercial coverage for scheduler-mutating paths above).
