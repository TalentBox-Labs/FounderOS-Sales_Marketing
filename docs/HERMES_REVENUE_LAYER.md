# Hermes Revenue Operating System (Phase 4)

## Overview

Hermes is the Chief Revenue Officer (CRO) layer of WorkCrew.ai's AI Executive Operating System. It orchestrates the entire lead-to-revenue pipeline:

**Lead → Score → Qualify → Deal → Close**

Hermes manages:
- **Lead Scoring** — Intelligent qualification (0-100 points)
- **Deal Automation** — Auto-create opportunities from qualified leads
- **Pipeline Health** — Real-time visibility into revenue metrics
- **Deal Velocity** — Track pipeline progression and forecast accuracy
- **Sales Crew** — SDR agents for autonomous outreach

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Incoming Leads (Web form, LinkedIn, Scraper, MCP APIs)     │
├─────────────────────────────────────────────────────────────┤
│ Lead Scoring Engine                                         │
│ - Source quality (0-30 pts)                                 │
│ - Engagement signals (0-40 pts)                             │
│ - Company fit (0-20 pts)                                    │
│ - Timing signals (0-10 pts)                                 │
├─────────────────────────────────────────────────────────────┤
│ Contact Status Updates (LEAD → PROSPECT → QUALIFIED)        │
├─────────────────────────────────────────────────────────────┤
│ Deal Automation (Qualified → Create Opportunity)            │
├─────────────────────────────────────────────────────────────┤
│ SDR Crew (Personalized Outreach)                            │
├─────────────────────────────────────────────────────────────┤
│ Pipeline Management (Track stages, forecast, velocity)      │
├─────────────────────────────────────────────────────────────┤
│ Hermes API (Revenue insights & recommendations)             │
└─────────────────────────────────────────────────────────────┘
```

---

## Lead Scoring Engine

### Scoring Methodology

Leads are scored 0-100 based on four dimensions:

#### 1. Source Quality (0-30 points)
```
Referral:        28 pts  ★★★★★  (Warm, vetted)
LinkedIn:        25 pts  ★★★★   (High intent, direct)
Web Form:        20 pts  ★★★    (Self-identified)
Manual:          12 pts  ★★     (Low intent)
Outreach:        15 pts  ★★     (Cold response)
Import:          10 pts  ★      (Bulk, unqualified)
API/N8N:          5 pts  ▢      (Automated)
```

#### 2. Engagement Signals (0-40 points)
- Email address: +10 pts
- LinkedIn profile: +10 pts
- Recent contact (≤7 days): +15 pts
- Recent (≤30 days): +8 pts
- Status PROSPECT: +5 pts
- Status QUALIFIED: +10 pts

#### 3. Company Fit (0-20 points)
- Revenue >$1M: +8 pts
- Funded (Series A+): +7 pts
- Active hiring: +5 pts

#### 4. Timing Signals (0-10 points)
- Fresh lead (≤7 days): +10 pts
- Recent (≤30 days): +6 pts
- Warm (≤90 days): +2 pts

### Score to Status Mapping

```
Score < 40    → LEAD      (Cold, need nurturing)
Score 40-70   → PROSPECT  (Warm, has interest)
Score 70-100  → QUALIFIED (Hot, ready for sales)
```

### Using Lead Scoring

```python
from revenue_os.services.lead_scoring_service import score_contact

# Score a single contact
score = score_contact(db, contact)
# Returns: 75 (QUALIFIED)

# Score multiple contacts
results = score_contacts_batch(db, contact_ids)
# Returns: {"scored": 150, "newly_qualified": 23, "scores": {...}}

# Get all high-scoring leads
leads = get_contacts_by_score(db, min_score=70, status=[ContactStatus.QUALIFIED])

# Get score distribution
dist = get_score_distribution(db)
# Returns: {"0-25": 45, "25-50": 120, "50-70": 80, "70-85": 35, "85-100": 12}
```

---

## Deal Automation

### Lead → Opportunity Conversion

When a contact reaches QUALIFIED status, Hermes automatically creates a Deal:

```python
from revenue_os.services.deal_automation_service import create_deal_from_contact

deal = create_deal_from_contact(db, contact, value=5000.0, owner_id=None)
# Creates: DISCOVERY stage deal with 20% probability
```

### Deal Lifecycle

```
DISCOVERY   → QUALIFIED  → PROPOSAL  → NEGOTIATION → CLOSED_WON
   20%          40%         60%         80%           100%
```

### Pipeline Health Metrics

```python
health = get_pipeline_health(db)
# Returns:
{
    "total_deals": 45,
    "total_pipeline_value": 225000.0,
    "weighted_forecast": 135000.0,  # Sum of deal values × probability
    "by_stage": {
        "discovery": {
            "count": 15,
            "total_value": 75000.0,
            "forecast": 15000.0
        },
        "negotiation": {
            "count": 8,
            "total_value": 50000.0,
            "forecast": 40000.0
        }
    }
}
```

### Deal Velocity Analysis

```python
velocity = calculate_deal_velocity(db, days=90)
# Returns:
{
    "period_days": 90,
    "closed_deals": 12,
    "won_deals": 9,
    "lost_deals": 3,
    "win_rate": 0.75,
    "avg_cycle_time_days": 45
}
```

---

## Hermes CRO API

### 1. Score Contacts

**POST /api/v1/hermes/score-contacts**

Score multiple contacts and update their qualification status.

```json
{
    "contact_ids": ["uuid1", "uuid2", "uuid3"],
    "company_context": {}
}
```

Response:
```json
{
    "ok": true,
    "total_scored": 3,
    "newly_qualified": 1,
    "scores": {
        "uuid1": {"score": 75, "status": "qualified"},
        "uuid2": {"score": 45, "status": "prospect"}
    }
}
```

### 2. Get Lead Scores

**GET /api/v1/hermes/lead-scores**

Fetch contacts within a score range.

Parameters:
- `min_score`: 0-100 (default: 0)
- `max_score`: 0-100 (default: 100)
- `status`: lead|prospect|qualified (optional)
- `limit`: 1-500 (default: 50)

```bash
curl "https://api.workcrew.ai/api/v1/hermes/lead-scores?min_score=70&status=qualified"
```

### 3. Score Distribution

**GET /api/v1/hermes/score-distribution**

Get histogram of lead scores across all contacts.

```json
{
    "ok": true,
    "distribution": {
        "0-25": 45,
        "25-50": 120,
        "50-70": 80,
        "70-85": 35,
        "85-100": 12
    }
}
```

### 4. Qualify Contacts

**POST /api/v1/hermes/qualify-contacts**

Create deals from qualified contacts.

```json
{
    "contact_ids": ["uuid1", "uuid2"],
    "default_value": 5000.0
}
```

Response:
```json
{
    "ok": true,
    "created": 2,
    "skipped": 0,
    "deals": [
        {
            "deal_id": "deal-uuid",
            "contact_id": "contact-uuid",
            "value": 5000.0,
            "stage": "discovery"
        }
    ]
}
```

### 5. Pipeline Health

**GET /api/v1/hermes/pipeline-health**

Real-time pipeline status and revenue forecast.

```json
{
    "ok": true,
    "total_pipeline_value": 225000.0,
    "weighted_forecast": 135000.0,
    "total_deals": 45,
    "by_stage": {
        "discovery": {...},
        "negotiation": {...}
    },
    "velocity": {
        "avg_cycle_days": 45,
        "win_rate": 0.75,
        "closed_this_period": 12
    }
}
```

### 6. Pipeline Forecast

**GET /api/v1/hermes/pipeline-forecast?days=90**

Project revenue for next N days.

### 7. Deals at Risk

**GET /api/v1/hermes/deals-at-risk**

Identify deals past due date or stale.

```json
{
    "ok": true,
    "count": 3,
    "total_value_at_risk": 45000.0,
    "deals": [
        {
            "deal_id": "uuid",
            "name": "ACME Corp - Enterprise License",
            "stage": "negotiation",
            "value": 25000.0,
            "risk_score": 45,
            "days_overdue": 12
        }
    ]
}
```

### 8. Revenue Summary

**GET /api/v1/hermes/revenue-summary**

Comprehensive dashboard for Paperclip (CEO) and Hermes (CRO).

```json
{
    "ok": true,
    "pipeline": {
        "total_value": 225000.0,
        "forecast": 135000.0,
        "deals": 45
    },
    "velocity": {
        "avg_cycle_days": 45,
        "win_rate": 0.75,
        "closed_this_period": 12
    },
    "funnel": {
        "total_leads": 500,
        "qualified_leads": 45,
        "deals_created": 45,
        "qualification_rate": 9.0,
        "deal_creation_rate": 100.0
    },
    "lead_quality": {
        "0-25": 45,
        "25-50": 120,
        "50-70": 80,
        "70-85": 35,
        "85-100": 12
    },
    "at_risk_deals": {
        "count": 3,
        "total_value": 45000.0
    }
}
```

### 9. SDR Outreach

**POST /api/v1/hermes/sdr-outreach**

Trigger autonomous SDR crew for personalized outreach.

```json
{
    "contact_id": "contact-uuid",
    "use_llm": true
}
```

---

## SDR Crew (Sales Development Rep)

The SDR Crew handles autonomous lead outreach:

### 1. Researcher Agent
- Analyzes company and prospect
- Identifies pain points
- Gathers context for personalization

### 2. Personalizer Agent
- Crafts compelling outreach messages
- References specific company initiatives
- Includes clear call-to-action

### 3. Scheduler Agent
- Plans outreach sequence (email, LinkedIn, follow-ups)
- Tracks engagement timing
- Schedules follow-up activities

### Usage

```python
from src.sdr_crew import SDRCrew

sdr = SDRCrew()
result = sdr.run_sdr_outreach(
    contact_name="John Smith",
    company_name="Acme Corp",
    role="VP of Engineering",
    email="john@acme.com",
    linkedin_url="https://linkedin.com/in/johnsmith"
)
# Returns: {"ok": true, "output": "Research + personalized message + schedule"}
```

Or via API:

```bash
curl -X POST https://api.workcrew.ai/api/v1/hermes/sdr-outreach \
  -H "Authorization: Bearer API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contact_id": "uuid",
    "use_llm": true
  }'
```

---

## Integration Examples

### Complete Lead-to-Revenue Flow

```python
from revenue_os.services.lead_scoring_service import score_contacts_batch
from revenue_os.services.deal_automation_service import create_deal_from_contact

# 1. Score new contacts
results = score_contacts_batch(db, new_contact_ids)
print(f"Newly qualified: {results['newly_qualified']}")

# 2. Get qualified contacts
qualified = get_contacts_by_score(db, min_score=70, status=[ContactStatus.QUALIFIED])

# 3. Create deals
for contact in qualified:
    deal = create_deal_from_contact(db, contact, value=5000.0)
    print(f"Created deal: {deal.name}")

# 4. Trigger SDR outreach
for contact in qualified:
    sdr = SDRCrew()
    sdr.run_sdr_outreach(
        contact_name=contact.full_name,
        company_name=contact.company.name,
        role=contact.designation,
        email=contact.email,
        linkedin_url=contact.linkedin_url
    )
```

### Dashboard Polling

```bash
# Get revenue summary every minute
watch -n 60 'curl -s -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/hermes/revenue-summary | jq'
```

### Risk Alerting

```python
import requests

# Get deals at risk
response = requests.get(
    "https://api.workcrew.ai/api/v1/hermes/deals-at-risk",
    headers={"Authorization": "Bearer API_KEY"}
)

at_risk = response.json()
if at_risk["count"] > 0:
    # Alert Hermes/sales team
    send_slack(f"⚠️ {at_risk['count']} deals at risk: ${at_risk['total_value_at_risk']}")
```

---

## Performance & Forecasting

### Win Rate Calculation

```
Win Rate = Closed Won Deals / Total Closed Deals (last 90 days)
```

### Forecast Accuracy

```
Accuracy = (Predicted Closed Value) / (Actual Closed Value)
Improves as historical data accumulates
```

### Cycle Time

```
Avg Cycle = Total Days / Number of Closed Deals
Used to estimate close dates for deals in progress
```

---

## Best Practices

### 1. Regular Lead Scoring

Run scoring weekly to keep lead quality up-to-date:

```bash
POST /api/v1/hermes/score-contacts with all imported contacts
```

### 2. Automated Deal Creation

Create deals immediately when contacts qualify:

```
Trigger: Contact.status → QUALIFIED
Action: POST /api/v1/hermes/qualify-contacts
```

### 3. Risk Monitoring

Check for at-risk deals daily:

```bash
GET /api/v1/hermes/deals-at-risk
Action on: risk_score > 30
```

### 4. Sales Enablement

Trigger SDR crew for high-priority leads:

```
Trigger: Contact.lead_score >= 80 AND status == QUALIFIED
Action: POST /api/v1/hermes/sdr-outreach
```

### 5. Revenue Forecasting

Update forecast weekly based on pipeline velocity:

```bash
GET /api/v1/hermes/pipeline-forecast?days=90
Adjust: Sales targets if forecast < goal
```

---

## Configuration

No special configuration needed. Hermes uses existing CRM models:

- `revenue_os.models.contact.Contact` (with `lead_score`, `status`)
- `revenue_os.models.deal.Deal` (with `stage`, `probability`, `value`)
- `revenue_os.models.company.Company` (with company fit data)

---

## Monitoring

### Key Metrics

- **Lead Volume**: New contacts imported
- **Qualification Rate**: % of leads reaching QUALIFIED
- **Pipeline Value**: Sum of all open deal values
- **Forecast**: Weighted expected revenue (value × probability)
- **Win Rate**: % of closed deals won
- **Cycle Time**: Days from DISCOVERY to CLOSED
- **At-Risk Value**: $ amount of overdue deals

### SLOs

- Score new contacts: < 1 minute
- Create deals from qualified: < 5 minutes
- SDR outreach execution: < 2 hours
- Pipeline health API: < 500ms response
- Forecast accuracy: > 80% (after 90 days data)

---

## Next Steps (Phase 5)

- Customer Success agent (churn detection, expansion)
- Marketing attribution (campaign to revenue)
- Sales analytics (rep performance, deal scoring model improvements)
- Integration with external CRMs (HubSpot, Salesforce)
- Real-time notifications and alerts
