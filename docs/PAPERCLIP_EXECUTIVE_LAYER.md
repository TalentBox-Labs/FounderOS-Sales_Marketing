# Paperclip Executive Layer (Phase 6)

## Overview

Paperclip is the **AI CEO** (Chief Executive Officer) of WorkCrew.ai. It aggregates data from all systems, calculates strategic KPIs, generates insights, and provides recommendations for executive decision-making.

**Core Responsibility:** Transform raw operational data into strategic intelligence.

```
All Systems → Paperclip → KPIs → Insights → Recommendations → Strategic Decisions
```

---

## Architecture

### Data Flow

```
┌────────────────────────────────────────────────────────┐
│ OPERATIONAL DATA SOURCES                               │
│ • Hermes (revenue, pipeline, leads)                    │
│ • Metrics (system performance, crew efficiency)        │
│ • Automation (workflows, events, execution)            │
│ • CRM (contacts, deals, activities)                    │
└────────────────┬─────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────┐
│ KPI CALCULATOR                                        │
│ • Revenue KPIs (ARR, pipeline, forecast, win rate)   │
│ • Sales KPIs (cycle time, deal size, at-risk)        │
│ • Lead KPIs (qualification rate, quality)            │
│ • Operations KPIs (efficiency, uptime)               │
└────────────────┬─────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────┐
│ INSIGHT ENGINE                                        │
│ • Trend analysis (up/down/stable)                     │
│ • Anomaly detection (below target, at risk)           │
│ • Comparative analysis (vs benchmarks)                │
│ • Predictive signals (early warnings)                 │
└────────────────┬─────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────┐
│ PAPERCLIP DASHBOARD                                   │
│ • Executive summary with critical alerts              │
│ • Strategic recommendations                           │
│ • Health score and trends                             │
│ • Resource allocation guidance                        │
└────────────────────────────────────────────────────────┘
```

---

## Key Performance Indicators (KPIs)

### Revenue KPIs

#### 1. Annual Recurring Revenue (ARR)
- **Calculation:** Weighted forecast × win rate × 4
- **Target:** Monthly target × 12
- **Status:** Healthy if ARR ≥ 80% of target

Example:
```
Pipeline: $400,000
Win Rate: 75%
Weighted Forecast: $300,000
ARR: $300,000 × 0.75 × 4 = $900,000
Target: $100,000/month × 12 = $1.2M
Status: 75% of target → Warning
```

#### 2. Pipeline Value
- **Calculation:** Sum of all open deal values
- **Target:** 3× monthly revenue target
- **Status:** Healthy if pipeline ≥ target

#### 3. Weighted Forecast
- **Calculation:** Sum of (deal value × probability/100)
- **Target:** 1× monthly revenue target
- **Status:** Monthly revenue prediction

#### 4. Monthly Closed Revenue
- **Calculation:** Sum of deals closed in last 30 days
- **Target:** Monthly revenue target
- **Status:** Healthy if ≥ 80% of target

#### 5. Win Rate
- **Calculation:** Deals won / (deals won + deals lost)
- **Target:** 75%
- **Status:** Healthy if ≥ 70%
- **Benchmark:** Industry standard 70-80%

### Sales KPIs

#### 1. Total Open Deals
- **Calculation:** Count of deals in DISCOVERY through NEGOTIATION
- **Target:** 50 deals
- **Status:** Healthy if > 40 deals

#### 2. Average Deal Size
- **Calculation:** Total pipeline value / number of deals
- **Target:** $5,000
- **Status:** Healthy if > $4,500

#### 3. Sales Cycle (Days)
- **Calculation:** Average days from DISCOVERY to CLOSED
- **Target:** 45 days
- **Status:** Healthy if ≤ 50 days
- **Warning:** > 60 days indicates process bottleneck

#### 4. At-Risk Deals
- **Calculation:** Count of deals flagged as at-risk
- **Target:** 0
- **Status:** Critical if > 20% of pipeline, warning if > 10%

### Lead KPIs

#### 1. Total Leads
- **Calculation:** Count of all contacts with status LEAD, PROSPECT, or QUALIFIED
- **Target:** 500 leads
- **Status:** Healthy if > 500

#### 2. Qualified Leads
- **Calculation:** Count of contacts with status QUALIFIED
- **Target:** 50 leads
- **Status:** Healthy if > 40

#### 3. Qualification Rate
- **Calculation:** (Qualified leads / total leads) × 100
- **Target:** 10%
- **Status:** Healthy if ≥ 8%
- **Insight:** Low rate indicates quality issues; high rate indicates good sourcing

#### 4. Average Lead Score
- **Calculation:** Mean of all contact lead_score values
- **Target:** 50 points
- **Status:** Healthy if > 45

### Operations KPIs

#### 1. Crew Efficiency
- **Calculation:** Successful crew executions / total executions
- **Target:** 90%
- **Status:** Healthy if > 80%

#### 2. Content Velocity
- **Calculation:** Content pieces published per week
- **Target:** 10 pieces/week
- **Status:** Healthy if > 8/week

#### 3. System Uptime
- **Calculation:** Uptime percentage over last 30 days
- **Target:** 99.9%
- **Status:** Healthy if > 99.5%

---

## Insights & Recommendations

### Insight Types

Paperclip generates insights in 4 categories:

#### 1. Revenue Insights
- Forecast below/above target
- Win rate declining/improving
- Pipeline too thin for targets
- Closed deal velocity

**Example Insights:**
- "⚠️ Revenue forecast is 75% of target. Recommend increasing deal velocity."
- "✅ Revenue forecast exceeds target by 25%. Can safely pursue expansion."

#### 2. Sales Insights
- Deals at risk of being lost
- Sales cycle too long
- No deals closing
- Deal progression bottlenecks

**Example Insights:**
- "🔴 5 deals totaling $150K are at risk. Immediate action required."
- "⏱️ Sales cycle is 65 days vs 45-day target. Identify and fix bottleneck."

#### 3. Lead Insights
- Lead quality issues
- No new lead inflow
- Low qualification rates
- Lead source quality differences

**Example Insights:**
- "📊 Only 5% of leads are qualified. Improve lead scoring or lead sources."
- "⚠️ No new leads in 30 days. Prospecting campaigns may be stalled."

#### 4. Operations Insights
- Qualified leads not converting to deals
- Crew efficiency declining
- System performance issues
- Automation failures

**Example Insights:**
- "📈 Only 60% of qualified leads have deals. Automate deal creation for qualified leads."
- "⚠️ Crew efficiency at 75% vs 90% target. Investigate and retrain."

### Recommendation Framework

Every critical insight includes a specific recommendation:

```
Insight: "Revenue forecast is 70% of target ($70K vs $100K)"
Recommendation: "Increase deal velocity by 25%:
  1. Accelerate PROPOSAL stage (currently 2 weeks → 1 week)
  2. Add sales rep to NEGOTIATION (currently bottleneck)
  3. Increase new deal inflow by 30% (need ~15 new deals/month)"
```

---

## Paperclip API

### 1. Executive Dashboard

**GET /api/v1/paperclip/dashboard**

Comprehensive CEO view with all KPIs, insights, and critical alerts.

```bash
curl -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/paperclip/dashboard
```

Response:
```json
{
  "ok": true,
  "timestamp": "2024-06-16T18:45:00Z",
  "health_score": 72.5,
  "critical_issues": 2,
  "kpis": {
    "revenue": {
      "arr": {
        "name": "Annual Recurring Revenue",
        "value": 900000,
        "target": 1200000,
        "unit": "$",
        "vs_target": 75.0,
        "status": "warning"
      },
      "pipeline": {...},
      "forecast": {...},
      "win_rate": {...}
    },
    "sales": {...},
    "leads": {...},
    "operations": {...}
  },
  "insights": {
    "revenue": [
      {
        "title": "⚠️ Revenue Forecast Below Target",
        "description": "Forecast is $70K vs $100K target (70%)",
        "priority": "critical",
        "recommendation": "Increase deal velocity..."
      }
    ],
    "sales": [...],
    "leads": [...],
    "operations": [...]
  },
  "critical_alerts": [
    {
      "title": "🔴 Deals at Risk",
      "description": "5 deals totaling $150K are at-risk",
      "recommendation": "Escalate to sales leadership immediately"
    }
  ]
}
```

### 2. Get KPIs

**GET /api/v1/paperclip/kpis**

Get all KPIs or filter by category.

Parameters:
- `category`: revenue | sales | leads | operations (optional)

```bash
# All KPIs
curl -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/paperclip/kpis

# Revenue KPIs only
curl -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/paperclip/kpis?category=revenue
```

Response:
```json
{
  "ok": true,
  "kpis": {
    "revenue": {
      "arr": {...},
      "pipeline": {...},
      "forecast": {...}
    }
  }
}
```

### 3. Get Insights

**GET /api/v1/paperclip/insights**

Get insights with optional filters.

Parameters:
- `priority`: critical | high | medium | low (optional)
- `category`: revenue | sales | leads | operations (optional)

```bash
# All critical insights
curl -H "Authorization: Bearer API_KEY" \
  "https://api.workcrew.ai/api/v1/paperclip/insights?priority=critical"

# Revenue insights
curl -H "Authorization: Bearer API_KEY" \
  "https://api.workcrew.ai/api/v1/paperclip/insights?category=revenue"
```

### 4. Get Recommendations

**GET /api/v1/paperclip/recommendations**

Get strategic recommendations from all insights.

```bash
curl -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/paperclip/recommendations
```

Response:
```json
{
  "ok": true,
  "count": 8,
  "recommendations": [
    {
      "title": "⚠️ Revenue Forecast Below Target",
      "insight": "Current forecast is $70K (70% of $100K target)",
      "recommendation": "Increase deal velocity by 25%:
        1. Reduce PROPOSAL stage to 1 week (from 2)
        2. Add sales rep to NEGOTIATION stage
        3. Increase new deal inflow by 30% (need 15 new deals/month)",
      "priority": "critical",
      "category": "revenue"
    }
  ]
}
```

### 5. Health Score

**GET /api/v1/paperclip/health-score**

Get overall company health score (0-100).

```bash
curl -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/paperclip/health-score
```

Response:
```json
{
  "ok": true,
  "overall_score": 72.5,
  "by_category": {
    "revenue": 70.0,
    "sales": 75.0,
    "leads": 65.0,
    "operations": 85.0
  },
  "status": "At Risk"
}
```

Health Status Mapping:
- **90-100:** Excellent
- **75-90:** Good
- **60-75:** At Risk
- **40-60:** Critical
- **<40:** Emergency

### 6. Forecast Accuracy

**GET /api/v1/paperclip/forecast-accuracy**

Get forecast vs actual accuracy metrics.

```json
{
  "ok": true,
  "accuracy": 78.5,
  "trend": "improving",
  "last_period": {
    "predicted": 125000,
    "actual": 98000,
    "variance": -21.6
  },
  "recommendation": "Forecast improving. Sales cycle stabilizing."
}
```

### 7. Strategic Summary

**GET /api/v1/paperclip/strategic-summary**

High-level summary for board/investor updates.

```json
{
  "ok": true,
  "timestamp": "2024-06-16T18:45:00Z",
  "company_health": "At Risk",
  "health_score": 72.5,
  "key_metrics": {
    "arr": {...},
    "pipeline": {...},
    "win_rate": {...},
    "total_deals": {...}
  },
  "critical_issues": 2,
  "top_priorities": [
    "Increase deal velocity by 25%",
    "Escalate 5 at-risk deals ($150K)",
    "Improve lead quality (5% qualification rate)"
  ]
}
```

---

## Use Cases

### 1. Daily Executive Brief

```bash
# CEO checks status every morning
curl https://api.workcrew.ai/api/v1/paperclip/health-score

# If score < 70, drill into critical insights
curl https://api.workcrew.ai/api/v1/paperclip/insights?priority=critical
```

### 2. Weekly Strategic Review

```bash
# Get full dashboard for weekly leadership meeting
curl https://api.workcrew.ai/api/v1/paperclip/dashboard

# Present KPIs and recommendations to team
```

### 3. Monthly Board Meeting

```bash
# Get strategic summary for investor/board update
curl https://api.workcrew.ai/api/v1/paperclip/strategic-summary

# Focus on key metrics, trends, and top priorities
```

### 4. Quarterly Planning

```bash
# Get insights and recommendations for Q planning
curl https://api.workcrew.ai/api/v1/paperclip/recommendations

# Use insights to inform:
# - Revenue targets
# - Resource allocation
# - Product roadmap
# - Team expansion
```

### 5. Investment Decision Making

```bash
# Assess company health before major investments
curl https://api.workcrew.ai/api/v1/paperclip/health-score

# Check forecast accuracy before committing to growth
curl https://api.workcrew.ai/api/v1/paperclip/forecast-accuracy

# Review KPI trends to inform investment decisions
```

---

## Strategic Recommendations Guide

### How to Interpret Recommendations

Each recommendation has:
1. **Clear problem statement** (what's wrong)
2. **Root cause analysis** (why it's happening)
3. **Specific action items** (what to do)
4. **Expected impact** (how it helps)

### Priority Levels

- **🔴 Critical:** Requires immediate action, impacts business
- **🟡 High:** Address within 1 week, significant impact
- **🟠 Medium:** Address within 1 month, moderate impact
- **🟢 Low:** Nice to have, low impact

### Common Recommendation Patterns

#### Revenue Pattern: Low Forecast
```
Issue: Revenue forecast is below target
Pattern:
  1. If pipeline thin → Increase lead generation
  2. If deal velocity slow → Fix stage bottlenecks
  3. If win rate low → Improve sales process
  4. If closing slow → Accelerate negotiations
```

#### Sales Pattern: Deals at Risk
```
Issue: High percentage of deals past due
Pattern:
  1. Escalate to sales leadership
  2. Increase deal review frequency
  3. Add close date accountability
  4. Improve sales process/training
```

#### Lead Pattern: Low Quality
```
Issue: Low qualification rate
Pattern:
  1. Review lead scoring model
  2. Audit lead sources
  3. Improve lead research
  4. Increase inbound marketing
```

---

## Monitoring Dashboard Setup

### Real-time Monitoring

```bash
# Check health score every 1 hour
watch -n 3600 'curl -s -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/paperclip/health-score | jq'

# Alert if score drops below 70
curl https://api.workcrew.ai/api/v1/paperclip/health-score | \
  jq 'if .overall_score < 70 then "ALERT: Health score critical" else "OK" end'
```

### Weekly Report

```bash
#!/bin/bash
# Generate weekly Paperclip report

REPORT=$(curl -s -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/paperclip/strategic-summary)

echo "=== WEEKLY EXECUTIVE REPORT ==="
echo "$REPORT" | jq '.key_metrics'
echo ""
echo "=== CRITICAL ISSUES ==="
echo "$REPORT" | jq '.top_priorities'
```

---

## Integration with Other Systems

### From Hermes (CRO)
- Pipeline metrics
- Deal velocity
- Win rates
- Lead scores

### From Metrics System
- Crew efficiency
- System uptime
- Request latency
- Error rates

### From Automation
- Workflow execution metrics
- Action success rates
- Event frequency

### From CRM
- Contact data
- Deal progression
- Activity history

---

## Customization

### Custom KPI Targets

Paperclip uses default targets. Customize via environment:

```bash
export PAPERCLIP_MONTHLY_REVENUE_TARGET=150000
export PAPERCLIP_PIPELINE_MULTIPLE=4
export PAPERCLIP_WIN_RATE_TARGET=80
```

### Custom Insight Rules

Add custom insight generators:

```python
from revenue_os.executive.insights import Insight, InsightEngine

def analyze_custom_metric(db: Session) -> list[Insight]:
    """Generate custom insights."""
    insights = []
    # Custom logic here
    return insights

# Register with InsightEngine
InsightEngine.custom_analyzers.append(analyze_custom_metric)
```

---

## Troubleshooting

### Health Score Calculation

If health score seems wrong:
1. Check individual KPI values: `/api/v1/paperclip/kpis`
2. Verify vs targets (set in environment)
3. Check if KPI data is stale

### Missing Insights

If expecting insights but none appear:
1. Ensure data exists in CRM
2. Check if thresholds are met
3. Verify insight rules in `insights.py`

### Recommendation Quality

Recommendations improve with data:
- Need 30+ days of data for trends
- Need 10+ closed deals for win rate
- Need 100+ leads for quality patterns

---

## Next Steps

**Phase 7 Options:**

- **Customer Success Agent** — Churn detection, expansion
- **Advanced Forecasting** — ML-based revenue prediction
- **Scenario Planning** — "What-if" analysis tools
- **Integrations** — Connect to external systems (Slack, Salesforce, HubSpot)
- **Reporting Automation** — Scheduled board reports, investor updates
