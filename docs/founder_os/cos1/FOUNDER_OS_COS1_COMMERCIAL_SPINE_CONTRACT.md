# Founder OS COS-1 Commercial Spine Contract

**STATUS:** IMPLEMENTED (presentation / read-model)
**Baseline:** `99a657a`
**HTTP product:** `runner_api:app`

## Journey

QualifiedDemand (intake on People / Operator) → People → Person workspace → Research → Outreach → Follow-up → Reply → Meeting interest → Governed booking proposal → Human approval → Meeting outcome → Activity.

## Entities

Unchanged freeze: Organization tenant; Company CRM account; Contact person; Deal opportunity record. Lead/Opportunity aliases only. QD/CO events on `AgentActionLog`. Meeting = Activity + M4/calendar artifact.

## Read models

`founder_ui_read_model.py` adds presentation fields (`action_label`, `company_name`, `attention`, `journey`, `ai_work`, reply labels). Does not create SoT. Company names loaded via org-scoped `Contact` rows, not an unscoped Company list UI.

## Authority

Unchanged: proposal-only booking/send; empty approval POST; no Contact.status from COS-1 UI.
