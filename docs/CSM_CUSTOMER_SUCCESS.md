# Customer Success Manager (CSM) Layer (Phase 7)

## Overview

The **Customer Success Manager (CSM)** is responsible for ensuring customer happiness, preventing churn, and driving expansion revenue. CSM completes the revenue loop:

**Acquire (Hermes) → Keep (CSM) → Expand (CSM) → Sustain Growth**

```
Paperclip (Strategy)
     ↓
Hermes (Sales) → New Customers
     ↓
CSM (Success) → Keep & Expand Existing Customers
     ↓
Repeat → Sustainable Growth
```

---

## Architecture

### Account Health Model

CSM assesses each customer account using multiple signals:

```
Engagement Signals
├─ Recent contact activity (last 30 days)
├─ Contact quality (qualified contacts)
└─ Activity frequency

Product Usage Signals
├─ Pipeline value
├─ Active deals
└─ Deal stage progression

Support Signals
├─ Support tickets
├─ Response time
└─ Resolution rate

Payment Signals
├─ Payment history
├─ Contract status
└─ Renewal date

Expansion Signals
├─ Additional use cases
├─ Adjacent products
└─ New departments
```

### Health Score Calculation

```
Health Score = Weighted Average of Signals
Range: 0-100
  0-40   = Critical (immediate action needed)
  40-60  = At Risk (intervention required)
  60-100 = Healthy (maintain engagement)
```

### Churn Risk Scoring

```
Churn Risk = 100 - Health Score (inverse)
  0-30   = Low risk (healthy, engaged)
  30-70  = Moderate risk (at-risk accounts)
  70-100 = High risk (critical, at risk of leaving)
```

### Expansion Potential Scoring

```
Expansion Score = Based on positive signals
Range: 0-100
  0-30   = Low (unlikely to expand)
  30-70  = Moderate (potential exists)
  70-100 = High (strong expansion opportunity)
```

---

## Account Health System

### Health Signals

#### Positive Signals (+value)
- High engagement (>70% contacts active last 30 days)
- Multiple qualified contacts (3+)
- Active expansion deals in pipeline
- Established account (>1 year)
- High pipeline value (>$50K)

#### Negative Signals (-value)
- Low engagement (<20% contacts active)
- No qualified contacts
- No active deals
- New account (<3 months)
- Low pipeline value (<$5K)

### Health Status Mapping

| Score | Status | Action |
|-------|--------|--------|
| 75-100 | Healthy | Maintain engagement, explore expansion |
| 50-75 | At Risk | Investigate issues, create intervention plan |
| <50 | Critical | Immediate escalation, executive involvement |

---

## CSM API (7 Endpoints)

### 1. Get All Account Health

**GET /api/v1/csm/accounts/health**

Get health assessment for all customer accounts.

```bash
curl -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/csm/accounts/health
```

Response:
```json
{
  "ok": true,
  "total_accounts": 25,
  "healthy": 18,
  "at_risk": 5,
  "critical": 2,
  "accounts": [
    {
      "account_id": "company-uuid",
      "account_name": "Acme Corp",
      "health_score": 78.5,
      "health_status": "healthy",
      "churn_risk_score": 21.5,
      "expansion_score": 65.0,
      "signals": [
        {
          "name": "High engagement (>70%)",
          "value": 30,
          "weight": 0.2,
          "category": "engagement"
        }
      ]
    }
  ]
}
```

### 2. Get Account Health (Specific)

**GET /api/v1/csm/accounts/{account_id}/health**

Get detailed health for a specific account.

```bash
curl -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/csm/accounts/company-uuid/health
```

### 3. Get At-Risk Accounts

**GET /api/v1/csm/accounts/at-risk**

Get accounts at risk of churn.

Parameters:
- `threshold`: Churn risk threshold (0-100, default: 60)

```bash
curl -H "Authorization: Bearer API_KEY" \
  "https://api.workcrew.ai/api/v1/csm/accounts/at-risk?threshold=70"
```

Response:
```json
{
  "ok": true,
  "count": 5,
  "threshold": 70,
  "accounts": [
    {
      "account_name": "Example Corp",
      "churn_risk_score": 85.0,
      "health_score": 35.0,
      "signals": [
        "Low engagement (<20%)",
        "No qualified contacts",
        "No active deals"
      ]
    }
  ]
}
```

### 4. Get Expansion Opportunities

**GET /api/v1/csm/accounts/expansion-opportunities**

Get accounts with expansion potential.

Parameters:
- `threshold`: Expansion score threshold (0-100, default: 60)

```bash
curl -H "Authorization: Bearer API_KEY" \
  "https://api.workcrew.ai/api/v1/csm/accounts/expansion-opportunities?threshold=70"
```

Response:
```json
{
  "ok": true,
  "count": 8,
  "threshold": 70,
  "accounts": [
    {
      "account_name": "Growth Inc",
      "expansion_score": 82.0,
      "health_score": 85.0,
      "estimated_expansion_value": 25000
    }
  ]
}
```

### 5. Get Account Recommendations

**GET /api/v1/csm/accounts/{account_id}/recommendations**

Get specific recommendations for an account.

```bash
curl -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/csm/accounts/company-uuid/recommendations
```

Response:
```json
{
  "ok": true,
  "account_id": "company-uuid",
  "total_recommendations": 3,
  "by_type": {
    "retention": 1,
    "expansion": 1,
    "engagement": 1
  },
  "recommendations": [
    {
      "title": "🔴 Critical: High Churn Risk",
      "description": "Account shows signs of disengagement",
      "action_type": "retention",
      "priority": "critical",
      "estimated_effort": "4 hours",
      "specific_steps": [
        "Schedule executive check-in within 48 hours",
        "Review contract and renewal date",
        "Develop remediation plan"
      ]
    }
  ]
}
```

### 6. Get All Recommendations

**GET /api/v1/csm/recommendations/all**

Get all recommendations across all accounts.

```bash
curl -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/csm/recommendations/all
```

### 7. Get CSM Actions Summary

**GET /api/v1/csm/actions-summary**

Get summary of all CSM actions needed.

```json
{
  "ok": true,
  "summary": {
    "total_recommendations": 25,
    "by_priority": {
      "critical": 2,
      "high": 5,
      "medium": 12,
      "low": 6
    },
    "total_potential_value": 150000,
    "total_effort_hours": 85,
    "critical_actions": 2,
    "expansion_value": 75000
  }
}
```

### 8. Review Account

**POST /api/v1/csm/accounts/{account_id}/review**

Trigger detailed CSM crew review for an account.

```bash
curl -X POST -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/csm/accounts/company-uuid/review
```

### 9. CSM Health

**GET /api/v1/csm/health**

Get CSM system health and status.

```json
{
  "ok": true,
  "total_accounts": 25,
  "critical_accounts": 2,
  "expansion_opportunities": 8,
  "total_expansion_value": 200000,
  "status": "healthy"
}
```

---

## Recommendation Types

### 1. Retention Recommendations

**Purpose:** Prevent churn

**Triggers:**
- Churn risk > 80% → Critical intervention
- Churn risk 60-80% → High priority check-in
- Churn risk 40-60% → Business review recommended

**Actions:**
- Executive check-in
- Pain point analysis
- Remediation plan
- Dedicated CSM assignment
- Contract review

**Example:**
```
Title: 🔴 Critical: High Churn Risk
Account: Example Corp
Churn Risk: 85%
Actions:
1. Schedule executive check-in within 48 hours
2. Review contract renewal date
3. Identify specific pain points
4. Develop remediation plan
5. Assign dedicated CSM
```

### 2. Expansion Recommendations

**Purpose:** Drive revenue growth from existing customers

**Triggers:**
- Expansion score > 80% → High priority opportunity
- Expansion score 60-80% → Moderate opportunity
- Health score > 70 → Account can absorb expansion

**Actions:**
- Discovery call
- Expansion proposal
- PoC or trial
- Implementation planning

**Value:** Estimated annual value of expansion opportunity

**Example:**
```
Title: ✨ High Expansion Opportunity
Account: Growth Inc
Expansion Value: $25,000
Actions:
1. Schedule discovery with expansion champion
2. Understand adjacent use cases
3. Prepare expansion proposal
4. Present opportunity
5. Develop implementation plan
```

### 3. Engagement Recommendations

**Purpose:** Improve adoption and satisfaction

**Triggers:**
- Health score < 50 → Low engagement
- No recent activity > 30 days
- Adoption metrics declining

**Actions:**
- Adoption audit
- Training/resources
- Product demo
- Success milestones
- Check-in cadence

### 4. Check-In Recommendations

**Purpose:** Maintain relationship and align on goals

**Triggers:**
- Quarterly business reviews
- Annual renewal discussions
- Strategic planning sessions

**Actions:**
- QBR with stakeholders
- ROI review
- Roadmap discussion
- Goal alignment

---

## CSM Crew

The CSM Crew handles intelligent account analysis and recommendations:

### 1. Health Monitor Agent
- Analyzes account health signals
- Identifies trends and patterns
- Rates overall account health
- Flags concerning signals

### 2. Account Manager Agent
- Develops retention strategies
- Plans customer interventions
- Schedules check-ins
- Identifies success milestones

### 3. Expansion Specialist Agent
- Identifies expansion opportunities
- Analyzes adjacent use cases
- Calculates expansion value
- Develops expansion strategy

---

## Use Cases

### Daily CSM Operations

```bash
# Check critical accounts
curl https://api.workcrew.ai/api/v1/csm/accounts/at-risk?threshold=80

# Review recommended actions
curl https://api.workcrew.ai/api/v1/csm/actions-summary

# Get next steps
curl https://api.workcrew.ai/api/v1/csm/recommendations/all?priority=critical
```

### Weekly Planning

```bash
# Get all recommendations
curl https://api.workcrew.ai/api/v1/csm/recommendations/all

# Identify expansion opportunities
curl https://api.workcrew.ai/api/v1/csm/accounts/expansion-opportunities

# Plan workload
curl https://api.workcrew.ai/api/v1/csm/actions-summary
```

### Monthly Business Reviews

```bash
# Review account health
curl https://api.workcrew.ai/api/v1/csm/accounts/health

# Get detailed recommendations
curl https://api.workcrew.ai/api/v1/csm/accounts/{account_id}/recommendations

# Trigger comprehensive review
curl -X POST https://api.workcrew.ai/api/v1/csm/accounts/{account_id}/review
```

---

## Integration with Other Systems

### From Hermes (Sales)
- New customers created as deals close
- Pipeline for expansion
- Customer interactions

### From Automation
- Triggers for engagement workflows
- Retention campaign automation
- Expansion nurturing sequences

### From Paperclip (Strategy)
- Overall portfolio health
- Expansion targets
- Retention goals

### From Metrics
- Product usage data
- Support ticket sentiment
- System uptime impact

---

## Best Practices

### 1. Proactive Engagement

Don't wait for customers to reach out. Monitor health scores weekly.

```bash
# Weekly health check
curl https://api.workcrew.ai/api/v1/csm/accounts/health | jq '.critical'

# If critical accounts: escalate immediately
```

### 2. Data-Driven Decisions

Use health scores and signals to guide interventions.

**Don't:** Assume account is fine because they paid their bill
**Do:** Review health signals and engagement metrics regularly

### 3. Personalized Approaches

Different accounts need different approaches:

- **Healthy:** Maintain engagement, explore expansion
- **At-Risk:** Investigate root cause, create remediation plan
- **Critical:** Executive involvement, contract review

### 4. Regular Business Reviews

Schedule QBRs based on account importance and maturity:

- **Strategic accounts:** Monthly
- **Mid-market:** Quarterly
- **Small accounts:** As-needed

### 5. Track Expansion Progress

Expansion doesn't happen overnight. Build a pipeline:

- Opportunity identification
- Initial outreach
- Discovery meeting
- Proposal development
- Implementation

---

## Retention Playbook

### High-Risk Account (Churn Risk >70%)

**Timeline: 48 hours to 2 weeks**

1. **Day 1:** Executive reaches out
   - Call/meeting with decision maker
   - Listen for pain points
   - Acknowledge concerns
   
2. **Day 2-3:** Diagnosis phase
   - Root cause analysis
   - Product/process review
   - Customer interview
   
3. **Day 4-5:** Solution phase
   - Develop remediation plan
   - Present options
   - Secure commitment
   
4. **Week 2:** Implementation
   - Assign dedicated CSM
   - Create success plan
   - Weekly check-ins

---

## Expansion Playbook

### High-Opportunity Account (Expansion Score >70%)

**Timeline: 2-4 weeks**

1. **Week 1:** Discovery
   - Schedule call with expansion champion
   - Understand new use cases
   - Identify decision-makers
   
2. **Week 2:** Preparation
   - Research competitive landscape
   - Prepare expansion proposal
   - Develop PoC/trial plan
   
3. **Week 3:** Presentation
   - Present expansion opportunity
   - Demonstrate value
   - Address concerns
   
4. **Week 4:** Commitment
   - Secure signed proposal
   - Plan implementation
   - Kickoff expansion project

---

## Measurement & KPIs

### Success Metrics

- **Churn Rate:** % of accounts lost annually
- **Net Revenue Retention:** Revenue from existing + expansion - churn
- **Expansion Rate:** % of accounts with additional revenue
- **Health Score Trend:** Average account health improving/declining
- **CSM Efficiency:** Revenue per CSM
- **Time to Value:** Days from onboarding to first value

---

## Troubleshooting

### Health Score Too Low

**Causes:**
- Engagement signals missing
- No recent deal activity
- New account (early stage)

**Solutions:**
- Ensure contacts have recent activity
- Create active deals in pipeline
- Schedule engagement activities

### No Expansion Opportunities

**Causes:**
- Account not healthy enough
- Limited market opportunity
- Unarticulated needs

**Solutions:**
- Focus on retention first
- Conduct needs analysis
- Present use cases/case studies

### Low Adoption Despite Recommendations

**Causes:**
- Recommendations not actioned
- Resource constraints
- Product-fit issues

**Solutions:**
- Ensure CSM capacity
- Escalate critical accounts
- Review product alignment

---

## Next Steps (Phase 8)

Potential enhancements:

- **Advanced Forecasting** — ML-based churn prediction
- **Integrations** — Slack notifications, webhook automation
- **Reporting** — Automated CSM dashboards
- **Automation** — Trigger workflows on health changes
- **Multi-language** — Support international CSM teams
