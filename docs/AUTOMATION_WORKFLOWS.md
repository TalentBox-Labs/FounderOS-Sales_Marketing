# Automation & Workflows Engine (Phase 5)

## Overview

The Automation & Workflows Engine powers the autonomous operations of WorkCrew.ai's AI Executive Operating System. It connects all system components through event-driven workflows that automatically execute actions when conditions are met.

**Key Principle:** Events trigger conditions, conditions trigger actions.

```
Event (Lead Qualified)
    ↓
Workflow Evaluates Conditions
    ↓
If Matched: Execute Actions (Notify, Create Task, Trigger Crew)
```

---

## Architecture

### 3-Layer System

```
┌────────────────────────────────────────────────────────┐
│ EVENT BUS                                              │
│ Lead Scored, Deal Created, Status Changed, etc.        │
└──────────────────┬─────────────────────────────────────┘
                   │
┌──────────────────▼─────────────────────────────────────┐
│ WORKFLOW ENGINE                                        │
│ Match events against trigger conditions                │
│ Execute matching workflows                             │
└──────────────────┬─────────────────────────────────────┘
                   │
┌──────────────────▼─────────────────────────────────────┐
│ ACTION EXECUTOR                                        │
│ Send Email, Slack, Create Task, Trigger Crew, etc.    │
└────────────────────────────────────────────────────────┘
```

---

## Events

### Event Types

**Lead Events:**
- `lead_created` — New lead imported
- `lead_scored` — Lead score calculated
- `lead_qualified` — Contact reaches QUALIFIED status

**Contact Events:**
- `contact_status_changed` — Status changes (LEAD → PROSPECT → QUALIFIED)
- `contact_imported` — Bulk contact import
- `contact_enriched` — Contact data enriched

**Deal Events:**
- `deal_created` — Opportunity created from qualified lead
- `deal_stage_changed` — Deal advances through pipeline
- `deal_at_risk` — Deal flagged as at-risk
- `deal_closed` — Deal won or lost

**Crew Events:**
- `crew_started` — Crew execution started
- `crew_completed` — Crew execution completed
- `crew_failed` — Crew execution failed

**Marketing Events:**
- `content_generated` — Content generation completed
- `content_published` — Content published to platforms

**Outreach Events:**
- `outreach_started` — Outreach sequence initiated
- `outreach_completed` — Outreach sequence completed

### Event Structure

```python
Event(
    event_type=EventType.LEAD_QUALIFIED,
    source="lead_scoring_service",        # Where event originated
    entity_id="contact-uuid",             # What triggered it
    entity_type="contact",                # Type of entity
    priority=EventPriority.HIGH,          # CRITICAL / HIGH / MEDIUM / LOW
    data={                                # Event context
        "score": 85,
        "status": "qualified",
        "company_id": "company-uuid"
    },
    timestamp="2024-06-16T18:30:00Z"
)
```

### Emitting Events

Events are emitted from within business logic:

```python
from revenue_os.automation.events import emit_lead_qualified

# In lead scoring service
emit_lead_qualified(contact_id, company_id)

# In deal automation
emit_deal_created(deal_id, contact_id, value)

# In deal progression
emit_deal_stage_changed(deal_id, old_stage, new_stage, probability)
```

---

## Workflows

A workflow is a trigger → condition → action chain that executes automatically.

### Workflow Components

**1. Trigger**
- Event type that starts the workflow (e.g., `LEAD_QUALIFIED`)

**2. Conditions**
- Optional filters evaluated against event data
- Multiple conditions are AND-ed together

**3. Actions**
- What happens when trigger + conditions match
- Can have multiple actions (execute sequentially)

### Example Workflows

#### 1. Lead Qualified → Notify & Outreach

**When:** Contact reaches QUALIFIED status
**Actions:**
- Send Slack alert to #sales
- Create task for sales rep
- Trigger SDR crew for automated outreach

```yaml
Workflow: Lead Qualified → Notify & Outreach
Trigger: LEAD_QUALIFIED
Conditions: (none - all qualifies trigger it)
Actions:
  - SEND_SLACK: "🔥 Lead qualified: {entity_id} (Score: {score})"
  - CREATE_TASK: "Review qualified lead (due in 4 hours)"
  - TRIGGER_SDR: "Execute personalized outreach"
```

#### 2. Deal at Risk → Alert & Escalate

**When:** Deal flagged as at-risk AND risk score ≥ 30
**Actions:**
- Send urgent Slack alert
- Create escalation task

```yaml
Workflow: Deal at Risk → Alert & Escalate
Trigger: DEAL_AT_RISK
Conditions:
  - risk_score >= 30
Actions:
  - SEND_SLACK: "⚠️ Deal at risk: {entity_id} (Risk: {risk_score})"
  - CREATE_TASK: "Escalate deal - {days_overdue} days overdue"
```

#### 3. Deal Closed → Update & Celebrate

**When:** Deal closes (won or lost)
**Actions:**
- Notify team in Slack
- Create activity record
- Update forecasts

```yaml
Workflow: Deal Closed → Update & Celebrate
Trigger: DEAL_CLOSED
Conditions: (none)
Actions:
  - SEND_SLACK: "🎉 Deal closed: {entity_id} (Value: ${value})"
  - CREATE_ACTIVITY: "Deal closed successfully"
```

---

## Actions

### Built-in Action Types

#### 1. CREATE_TASK
Create a task for the team.

```json
{
  "action_type": "create_task",
  "config": {
    "title": "Review lead",
    "description": "New qualified lead from LinkedIn",
    "assigned_to": "sales-team@example.com",
    "due_in_hours": 24
  }
}
```

#### 2. SEND_EMAIL
Send email notification.

```json
{
  "action_type": "send_email",
  "config": {
    "to": "sales-team@example.com",
    "subject": "New qualified lead: {entity_id}",
    "body": "Contact {entity_id} has been qualified. Lead score: {score}"
  }
}
```

Supports template variables from event data: `{entity_id}`, `{score}`, `{status}`, etc.

#### 3. SEND_SLACK
Send Slack notification.

```json
{
  "action_type": "send_slack",
  "config": {
    "channel": "#sales",
    "message": "🔥 Lead qualified: {entity_id} (Score: {score})",
    "webhook_url": "https://hooks.slack.com/..."
  }
}
```

#### 4. TRIGGER_CREW
Trigger a crew to execute.

```json
{
  "action_type": "trigger_crew",
  "config": {
    "crew_name": "marketing",
    "params": {
      "brand": "workcrew",
      "topic": "AI Recruiting"
    }
  }
}
```

#### 5. TRIGGER_SDR
Trigger SDR crew for personalized outreach.

```json
{
  "action_type": "trigger_sdr",
  "config": {
    "use_llm": true
  }
}
```

#### 6. UPDATE_FIELD
Update a field on an entity.

```json
{
  "action_type": "update_field",
  "config": {
    "entity_type": "contact",
    "field": "owner_id",
    "value": "sales-rep-uuid"
  }
}
```

#### 7. CREATE_ACTIVITY
Create an activity record (email, call, task).

```json
{
  "action_type": "create_activity",
  "config": {
    "activity_type": "email",
    "subject": "Outreach email",
    "body": "Personalized message sent"
  }
}
```

---

## API Reference

### Create Workflow

**POST /api/v1/automation/workflows**

```json
{
  "name": "Lead Qualified → Outreach",
  "description": "When a lead qualifies, notify and trigger SDR",
  "event_type": "lead_qualified",
  "conditions": [],
  "actions": [
    {
      "action_type": "send_slack",
      "config": {
        "channel": "#sales",
        "message": "🔥 Lead qualified: {entity_id}"
      }
    },
    {
      "action_type": "trigger_sdr",
      "config": {"use_llm": true}
    }
  ],
  "enabled": true
}
```

Response:
```json
{
  "ok": true,
  "workflow": {
    "workflow_id": "wf_abc123",
    "name": "Lead Qualified → Outreach",
    "event_type": "lead_qualified",
    "enabled": true,
    "execution_count": 0
  }
}
```

### List Workflows

**GET /api/v1/automation/workflows**

```bash
curl -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/automation/workflows
```

### Get Workflow

**GET /api/v1/automation/workflows/{workflow_id}**

### Toggle Workflow

**PUT /api/v1/automation/workflows/{workflow_id}/toggle**

Enable/disable a workflow without deleting it.

### Delete Workflow

**DELETE /api/v1/automation/workflows/{workflow_id}**

### Preset Workflows

Create common workflows with one call:

```bash
# Lead Qualified workflow
POST /api/v1/automation/workflows/presets/lead-qualified

# Deal at Risk workflow
POST /api/v1/automation/workflows/presets/deal-at-risk

# Deal Closed workflow
POST /api/v1/automation/workflows/presets/deal-closed

# Crew Completed workflow
POST /api/v1/automation/workflows/presets/crew-completed
```

### Workflow Executions

**GET /api/v1/automation/workflows/{workflow_id}/executions**

Get execution history for a workflow.

```json
{
  "ok": true,
  "workflow_id": "wf_abc123",
  "execution_count": 15,
  "executions": [
    {
      "execution_id": "exec_xyz789",
      "workflow_id": "wf_abc123",
      "event_id": "evt_123456",
      "triggered_at": "2024-06-16T18:30:00Z",
      "status": "completed",
      "actions_executed": [
        {
          "action_id": "act_xyz",
          "action_type": "send_slack",
          "result": {"ok": true, "slack_message_id": "msg_123"}
        }
      ]
    }
  ]
}
```

### Event History

**GET /api/v1/automation/events/history**

Get recent events that triggered workflows.

Parameters:
- `event_type`: Filter by event type (optional)
- `limit`: Number of events to return (default: 50)

```bash
curl "https://api.workcrew.ai/api/v1/automation/events/history?event_type=lead_qualified&limit=20"
```

### List Event Types

**GET /api/v1/automation/events/types**

Get all available event types.

### List Action Types

**GET /api/v1/automation/actions/types**

Get all available action types.

### Automation Health

**GET /api/v1/automation/health**

Get automation system status.

```json
{
  "ok": true,
  "total_workflows": 8,
  "enabled_workflows": 7,
  "status": "healthy"
}
```

---

## Use Cases

### 1. Lead Nurturing Automation

**Problem:** New leads need immediate follow-up to convert.
**Solution:** Trigger SDR crew automatically when leads qualify.

```
IF contact.lead_score >= 70 AND status == QUALIFIED
THEN trigger SDR crew + send Slack alert + create task
```

### 2. Deal Health Monitoring

**Problem:** Sales team loses track of stalled deals.
**Solution:** Flag at-risk deals automatically.

```
IF deal.stage IN (PROPOSAL, NEGOTIATION) 
  AND days_in_stage > 14
  AND expected_close_date < today
THEN send alert + escalate to manager
```

### 3. Pipeline Forecasting

**Problem:** Sales forecasts become stale.
**Solution:** Update forecasts when deals close.

```
IF deal status == CLOSED
THEN update forecast + notify revenue ops
```

### 4. Content Distribution

**Problem:** Generated content needs to go to all channels.
**Solution:** Trigger publishing when content is ready.

```
IF crew_type == MARKETING AND crew_status == COMPLETED
THEN publish to social media + update CRM
```

### 5. Team Notifications

**Problem:** Team misses important events.
**Solution:** Send real-time Slack alerts.

```
IF lead.score >= 90
THEN send "Hot lead incoming" alert to #sales
```

---

## Conditions & Operators

### Operators

- `eq` — Equal to
- `gte` — Greater than or equal
- `lte` — Less than or equal
- `gt` — Greater than
- `lt` — Less than
- `contains` — String contains
- `in` — Value in list
- `exists` — Field exists (not null)

### Examples

```python
# Score is high
Condition("score", "gte", 70)

# Status is qualified
Condition("status", "eq", "qualified")

# Days overdue > 14
Condition("days_overdue", "gt", 14)

# Risk score at or above threshold
Condition("risk_score", "gte", 30)

# Stage is in late pipeline
Condition("stage", "in", ["proposal", "negotiation"])
```

---

## Template Variables

Actions support template variables from event data using `{variable_name}` syntax:

```json
{
  "message": "Lead {entity_id} qualified with score {score}"
}
```

**Available variables depend on event type:**

- `entity_id` — ID of entity that triggered event
- `entity_type` — Type of entity
- `event_type` — Type of event
- Event-specific data (see Event Structure)

---

## Execution Flow

1. **Event is emitted** — Business logic triggers event
2. **EventBus publishes** — Event added to bus
3. **WorkflowEngine evaluates** — All workflows check if they match
4. **Conditions evaluated** — If trigger matches, conditions are checked
5. **Actions executed** — If conditions pass, actions execute in sequence
6. **Execution logged** — Result recorded in execution history

---

## Monitoring & Debugging

### View Execution History

```bash
# Get workflow executions
curl -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/automation/workflows/wf_abc123/executions

# Get recent events
curl -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/automation/events/history?limit=50
```

### Enable/Disable Workflows

```bash
# Temporarily disable workflow without deleting
curl -X PUT -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/automation/workflows/wf_abc123/toggle
```

### Check System Health

```bash
curl -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/automation/health
```

---

## Best Practices

### 1. Be Specific with Conditions

Don't trigger on every event. Use conditions to narrow scope:

```python
# Good: Only notify on high-risk deals
Condition("risk_score", "gte", 30)

# Bad: Send alert on every deal update
# (no conditions)
```

### 2. Chain Actions Wisely

Order matters. Put critical actions first:

```python
# Good: Alert first, then create task
[
    SEND_SLACK,      # Immediate notification
    CREATE_TASK,     # Fallback if Slack fails
]

# Bad: Create task first, then alert
[
    CREATE_TASK,
    SEND_SLACK,      # If task creation fails, alert never sent
]
```

### 3. Test with Presets

Start with preset workflows to understand patterns:

```bash
POST /api/v1/automation/workflows/presets/lead-qualified
POST /api/v1/automation/workflows/presets/deal-at-risk
```

### 4. Monitor Execution History

Regularly check workflow executions to ensure they're working:

```bash
GET /api/v1/automation/workflows/{workflow_id}/executions
```

### 5. Use Templates for Dynamic Messages

Take advantage of event data in messages:

```json
{
  "message": "🔥 {entity_id} qualified from {source} (Score: {score})"
}
```

---

## Advanced: Custom Handlers

Extend the system with custom action handlers:

```python
from revenue_os.automation.actions import ActionExecutor, ActionType

def handle_custom_action(config: dict, context: dict):
    """Execute custom action."""
    # Implementation
    return {"ok": True, "result": "..."}

# Register handler
ActionExecutor.register_handler(ActionType.CUSTOM_ACTION, handle_custom_action)
```

---

## Troubleshooting

### Workflow Not Triggering

**Check:**
1. Is the workflow enabled?
2. Does the event type match?
3. Are all conditions being met?

```bash
# Check workflow status
GET /api/v1/automation/workflows/{workflow_id}

# Check recent events
GET /api/v1/automation/events/history
```

### Actions Not Executing

**Check:**
1. Is the action enabled?
2. Is the action handler registered?
3. Are template variables correct?

```bash
# Check action types available
GET /api/v1/automation/actions/types

# Check execution history
GET /api/v1/automation/workflows/{workflow_id}/executions
```

### Performance Issues

**Solutions:**
1. Disable unused workflows
2. Add conditions to reduce trigger frequency
3. Batch actions instead of individual notifications

---

## Roadmap

**Future enhancements:**
- Scheduled workflows (run on schedule, not events)
- Conditional branching (IF/THEN/ELSE)
- Multi-step approval workflows
- Webhook notifications
- Integration with external systems
- Workflow templates/marketplace
