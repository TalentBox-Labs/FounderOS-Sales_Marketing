# Autonomous AI Execution (Phase 11)

## Overview

Phase 11 adds **autonomous AI execution** to the operating system. Enable agents to independently execute tasks, make decisions, and drive business outcomes with built-in safeguards:

```
Tasks → Execution → Decisions → Approval → Action → Audit
```

---

## Core Concepts

### Autonomous Agents

Agents that:
- Execute tasks without constant human oversight
- Make decisions based on confidence levels
- Work collaboratively through workflows
- Report actions via audit logs
- Respect human-defined safeguards

### Agent Types

- **SDR (Sales Development)** - Outreach, lead qualification
- **CSM (Customer Success)** - Account management, health monitoring
- **Sales Manager** - Pipeline management, deal coaching
- **Finance** - Invoice processing, reconciliation
- **Product** - Feature prioritization, roadmap planning
- **Operations** - Process optimization, task automation

---

## Task Execution

### Creating Tasks

Tasks define work for agents:

```bash
curl -X POST -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/agents/tasks \
  -d '{
    "agent_type": "sdr",
    "title": "Outreach to hot prospects",
    "description": "Contact 10 new prospects in finance vertical",
    "priority": 4,
    "requires_approval": false,
    "metadata": {
      "vertical": "finance",
      "prospect_count": 10,
      "template": "cold_outreach_v2"
    }
  }'
```

### Task Properties

- **priority** - 1-5, 5 = highest
- **requires_approval** - Block execution pending review
- **metadata** - Custom context data

### Task Lifecycle

```
PENDING → RUNNING → COMPLETED
              ↓
           FAILED
              ↓
           BLOCKED
              ↓
           APPROVED → RUNNING
```

### Getting Pending Tasks

Agents poll for work:

```bash
curl -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/agents/tasks/sdr?limit=10
```

**Response:**
```json
{
  "ok": true,
  "agent_type": "sdr",
  "count": 3,
  "tasks": [
    {
      "id": "task_abc123",
      "title": "Outreach to hot prospects",
      "priority": 4,
      "status": "pending",
      "requires_approval": false
    }
  ]
}
```

### Completing Tasks

Report results:

```bash
curl -X POST -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/agents/tasks/{task_id}/complete \
  -d '{
    "result": {
      "contacts_reached": 8,
      "positive_responses": 3,
      "meetings_scheduled": 2
    }
  }'
```

---

## Autonomous Decisions

### Proposing Decisions

Agents propose actions with confidence levels:

```bash
curl -X POST -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/agents/decisions \
  -d '{
    "agent_type": "csm",
    "entity_id": "company_123",
    "entity_type": "account",
    "decision": "schedule_health_check_call",
    "confidence": 0.92,
    "reasoning": "Account health score dropped 15 points, no activity 14 days",
    "alternative_actions": [
      "send_health_check_email",
      "schedule_expansion_discussion"
    ]
  }'
```

### Decision Flow

**High Confidence (≥80%):**
- Auto-approved
- Immediately executed
- Logged for audit

**Medium Confidence (60-80%):**
- Pending approval queue
- Human reviews context
- Approved or rejected

**Low Confidence (<60%):**
- Always pending approval
- Human makes final decision
- Provides alternatives

### Approving Decisions

Review and approve:

```bash
curl -X POST -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/agents/decisions/{decision_id}/approve \
  -d '{
    "approved_by": "sarah@company.com"
  }'
```

### Getting Pending Decisions

```bash
curl -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/agents/decisions/pending?limit=20
```

---

## Multi-Agent Workflows

### Workflow Strategies

#### Sequential
Agents execute one after another:
```
Agent A → Agent B → Agent C
```
Use for: Dependency chains (research → draft → review)

#### Parallel
All agents execute simultaneously:
```
Agent A ┐
Agent B ├→ Combine results
Agent C ┘
```
Use for: Independent analysis (sales → CSM → finance)

#### Hierarchical
Manager delegates to team:
```
Manager Agent
  ├→ Team Agent A
  ├→ Team Agent B
  └→ Team Agent C
```
Use for: Coordinated team efforts

#### Consensus
All agents vote:
```
Agent A: "approve"
Agent B: "approve"
Agent C: "reject"
→ 2/3 = approved (67%)
```
Use for: Important decisions

### Creating Workflows

```bash
curl -X POST -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/agents/workflows \
  -d '{
    "name": "Deal Risk Assessment",
    "description": "Multi-agent analysis of at-risk deals",
    "strategy": "parallel",
    "agents": ["sales_manager", "csm", "finance"],
    "trigger_condition": "deal.win_probability < 0.3"
  }'
```

### Executing Workflows

```bash
curl -X POST -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/agents/workflows/{workflow_id}/execute \
  -d '{
    "context": {
      "deal_id": "deal_123",
      "deal_value": 100000,
      "win_probability": 0.25
    }
  }'
```

**Response:**
```json
{
  "ok": true,
  "execution": {
    "id": "exec_xyz789",
    "workflow_id": "wf_abc123",
    "status": "completed",
    "final_decision": "increase_engagement",
    "confidence": 0.87,
    "agent_results": {
      "sales_manager": {...},
      "csm": {...},
      "finance": {...}
    }
  }
}
```

---

## Safeguards

### Safeguard Rules

Restrict agent actions:

```bash
curl -X POST -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/agents/safeguards/rules \
  -d '{
    "name": "Max deal discount",
    "description": "Prevent discounts >20%",
    "rule_type": "max_value",
    "condition": "context['discount_percent'] > 20",
    "action": "block"
  }'
```

### Rule Types

- **max_value** - Limit transaction size
- **budget** - Stay within spend limits
- **approval_required** - Require human approval
- **customer_type** - Restrict by customer segment
- **threshold** - Alert if metric crosses threshold

### Actions

- **block** - Reject action immediately
- **alert** - Log warning, allow action
- **require_approval** - Queue for human review

### Checking Safeguards

Before executing:

```bash
curl -X POST -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/agents/safeguards/check \
  -d '{
    "agent_name": "sdr_bot_1",
    "task_id": "task_abc123",
    "action": "send_email",
    "context": {
      "recipient_count": 100,
      "email_type": "promotional"
    }
  }'
```

**Response:**
```json
{
  "ok": true,
  "allowed": true,
  "violations": []
}
```

---

## Monitoring

### Agent Health

Monitor real-time agent health:

```bash
curl -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/agents/monitor/health
```

**Response:**
```json
{
  "ok": true,
  "agents": {
    "sdr_bot_1": {
      "status": "healthy",
      "metrics_count": 25,
      "anomalies_1h": 0,
      "last_updated": "2026-06-17T10:30:00Z"
    },
    "csm_bot_1": {
      "status": "degraded",
      "metrics_count": 18,
      "anomalies_1h": 2,
      "last_updated": "2026-06-17T10:28:00Z"
    }
  }
}
```

### Health Status

- **healthy** - Normal operation
- **degraded** - Occasional anomalies (3-5/hour)
- **critical** - Frequent anomalies (>5/hour)

### Performance Metrics

Track agent effectiveness:

```bash
curl -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/agents/performance
```

**Metrics:**
- Total tasks completed
- Success rate
- Average decision confidence
- Total value generated
- Approval rate

### Audit Trail

Complete action history:

```bash
curl -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/agents/audit/{agent_name}?limit=100
```

**Logged:**
- Agent, action, entity
- Result (success/failure)
- Timestamp
- Metadata

---

## API Reference

### Task Management

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/agents/tasks` | Create task |
| GET | `/api/v1/agents/tasks/{agent_type}` | Get pending tasks |
| POST | `/api/v1/agents/tasks/{id}/complete` | Complete task |

### Decision Management

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/agents/decisions` | Propose decision |
| GET | `/api/v1/agents/decisions/pending` | Get pending approvals |
| POST | `/api/v1/agents/decisions/{id}/approve` | Approve decision |

### Workflow Management

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/agents/workflows` | Create workflow |
| GET | `/api/v1/agents/workflows` | List workflows |
| POST | `/api/v1/agents/workflows/{id}/execute` | Run workflow |

### Safeguards

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/agents/safeguards/rules` | Add rule |
| GET | `/api/v1/agents/safeguards/rules` | List rules |
| POST | `/api/v1/agents/safeguards/check` | Check action |

### Monitoring

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v1/agents/monitor/{name}/health` | Agent health |
| GET | `/api/v1/agents/monitor/health` | All agent health |
| GET | `/api/v1/agents/audit/{name}` | Audit trail |
| GET | `/api/v1/agents/performance` | Performance metrics |
| GET | `/api/v1/agents/health` | System health |

---

## Use Cases

### Autonomous Outreach

**Workflow:**
```
1. SDR identifies prospects (automated)
2. Creates personalized emails (AI-generated)
3. Schedules sends (autonomous)
4. Logs all interactions (audit trail)
5. CSM notified of qualified leads
```

### Churn Prevention

**Workflow:**
```
1. CSM detects at-risk account
2. Proposes intervention (health check call)
3. High confidence → auto-scheduled
4. Low confidence → pending approval
5. Action tracked and measured
```

### Deal Risk Management

**Workflow:**
```
1. Sales Manager detects at-risk deal
2. Sales + CSM + Finance analyze (parallel)
3. Consensus decision on action
4. Execute with safeguards
5. Track outcome
```

### Customer Engagement

**Workflow:**
```
1. Product Agent analyzes usage
2. CSM Agent evaluates health
3. Finance Agent checks expansion potential
4. Decision: which customer to contact
5. Action: send targeted offer
```

---

## Best Practices

### Confidence Thresholds

- **>85%** - Auto-execute critical path
- **70-85%** - Low-risk actions, auto-execute
- **50-70%** - Medium-risk, pending approval
- **<50%** - High-risk, always require approval

### Safeguard Defaults

- All decisions > $10K require approval
- All customer contact > 100 requires approval
- All refunds > $1K require approval
- All customer data export requires approval

### Monitoring

- Check health every 5 minutes
- Alert if status degraded >30 minutes
- Review anomalies daily
- Audit log retention: 90 days

### Escalation

- Block high-risk actions immediately
- Alert for medium-risk violations
- Require human approval for sensitive decisions
- Log all overrides

---

## Troubleshooting

### Agent Not Executing

**Check:**
- Task status in queue
- Safeguard violations
- Agent health status
- Audit logs

### Decision Approval Stuck

**Check:**
- Decision still pending
- Review queue not processed
- Confidence level correct
- Safeguards not blocking

### Low Performance

**Check:**
- Success rate metrics
- Decision approval rate
- Confidence scoring
- Anomaly patterns

---

## Future Enhancements

- Real-time learning from outcomes
- Dynamic confidence calibration
- Cross-agent communication
- Predictive task generation
- Advanced anomaly detection
- Custom decision frameworks
- Integration with external systems
- Collaborative human-AI workflows
