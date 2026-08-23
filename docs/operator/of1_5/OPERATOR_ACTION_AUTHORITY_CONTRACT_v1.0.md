# OPERATOR ACTION AUTHORITY CONTRACT v1.0

**STATUS: FROZEN**

## Implementation map (UI → API → domain → SoT → audit → authority)

| UI action | Operator API | Canonical operation | SoT | Audit | Authority |
|-----------|--------------|---------------------|-----|-------|-----------|
| Accept demand | `POST /api/v1/operator/actions/qualified-demand/accept` | `accept_qualified_demand` | Contact + `AgentActionLog` | `qualified_demand_accepted` | Trusted human env |
| Reject demand | `POST /api/v1/operator/actions/qualified-demand/reject` | `reject_qualified_demand` | `AgentActionLog` | `qualified_demand_rejected` | Trusted human env |
| Update status | `POST /api/v1/operator/actions/contact-status` | `apply_contact_status_update` | Contact | A4.5 / EventBus | Trusted human env |
| Create deal | `POST /api/v1/operator/actions/deal/create` | Deal ORM + `get_or_create_sales_pipeline` | Deal | create response `created_by` | Trusted human env; non-terminal stages only |
| Update stage | `POST /api/v1/operator/actions/deal/stage` | `apply_deal_stage_update` | Deal | A3.5 (`commercial_outcome_emitted: false`) | Trusted human env |
| CO handoff | `POST /api/v1/operator/actions/commercial-outcome/handoff` | `register_commercial_outcome_handoff` | `AgentActionLog` | `commercial_outcome_handoff` | Trusted human env; Deal must be `closed_won` |
| CO accept | `POST /api/v1/operator/actions/commercial-outcome/accept` | `accept_commercial_outcome` | `AgentActionLog` | `commercial_outcome_accepted` | Trusted human env |
| CO reject | `POST /api/v1/operator/actions/commercial-outcome/reject` | `reject_commercial_outcome` | `AgentActionLog` | `commercial_outcome_rejected` | Trusted human env |

Template `ofPost` sends only action fields. **No `requested_by` in browser payloads.**

| Actor | Mutations |
|-------|-----------|
| `FOUNDER_OS_OPERATOR_NAME` valid human | Permitted |
| Agent / AI / spoofed env | 503 |
| Client `requested_by` / `human=true` | Ignored / not accepted |
| Direct service call without human | `HumanAuthorityError` (UI1.1) |
