# Reporting Automation (Phase 10)

## Overview

Phase 10 adds **automated report generation and distribution** to the AI Executive Operating System. Transform raw data into actionable insights delivered to stakeholders automatically:

```
Data → Reports → Schedule → Deliver → Measure Impact
```

---

## Report Types

### 1. Executive Briefing
**Target:** C-suite (CEO, CFO, CMO)

Daily/Weekly summary:
- Revenue metrics and KPIs
- Pipeline health snapshot
- Critical alerts
- Strategic recommendations

### 2. Sales Pipeline Report
**Target:** Sales leadership, individual reps

Weekly detailed view:
- Deal progression by stage
- At-risk deals with action items
- Win rate trends
- Pipeline coverage analysis

### 3. Customer Health Report
**Target:** CSM team, customer success leadership

Weekly account health:
- Health score breakdown
- Churn risk alerts
- Expansion opportunities
- Action items by account

### 4. Revenue Forecast Report
**Target:** Finance, leadership

Monthly detailed forecast:
- 3-6 month forecast with confidence intervals
- Scenario analysis impact
- Historical accuracy
- Risk factors

### 5. Churn Risk Report
**Target:** CSM leadership, executives

Weekly at-risk analysis:
- High-risk accounts (>70% churn probability)
- Contributing factors
- Recommended interventions
- Success metrics

### 6. Team Performance Report
**Target:** Sales managers, team leads

Monthly team metrics:
- Individual quota attainment
- Deal velocity
- Win rate comparison
- Activity metrics

### 7. Expansion Opportunities Report
**Target:** Sales leadership, CSM team

Monthly expansion view:
- High-probability expansion targets
- Upsell/cross-sell opportunities
- Customer readiness assessment
- Revenue potential

### 8. Weekly Digest
**Target:** All staff

Summary for everyone:
- Key metrics
- Deal wins and losses
- Top performers
- Important announcements

### 9. Monthly Review
**Target:** All staff

Comprehensive monthly retrospective:
- Full month metrics
- Trends vs. last month
- Team achievements
- Outlook for next month

---

## Report Templates

### Creating Templates

```bash
curl -X POST -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/reporting/templates/register \
  -d '{
    "name": "executive_briefing",
    "report_type": "executive_briefing",
    "title": "Executive Briefing",
    "description": "Daily executive summary",
    "color_scheme": "professional",
    "logo_url": "https://example.com/logo.png",
    "footer_text": "Confidential - For internal use only",
    "sections": [
      {
        "title": "Revenue Metrics",
        "description": "Key revenue KPIs",
        "data_source": "kpi",
        "visualization": "chart",
        "parameters": {
          "metrics": ["arr", "pipeline", "forecast", "win_rate"],
          "period": "monthly"
        }
      },
      {
        "title": "Executive Insights",
        "description": "Key insights and recommendations",
        "data_source": "insight",
        "visualization": "list",
        "parameters": {
          "category": "executive",
          "limit": 5
        }
      },
      {
        "title": "At-Risk Accounts",
        "description": "Accounts flagged for attention",
        "data_source": "metric",
        "visualization": "table",
        "parameters": {
          "filter": "at_risk",
          "limit": 10
        }
      }
    ]
  }'
```

### Template Components

Each section specifies:
- **title**: Section heading
- **description**: Section purpose
- **data_source**: Where data comes from (kpi, insight, metric, forecast, table)
- **visualization**: How to display (chart, table, list, graph)
- **parameters**: Data-specific parameters

### Color Schemes

- `professional`: Gray/blue (default)
- `colorful`: Multi-color, modern
- `minimal`: Black/white, clean

---

## Generating Reports

### On-Demand Generation

Generate report immediately:

```bash
curl -X POST -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/reporting/generate \
  -d '{
    "template_name": "executive_briefing",
    "format": "html",
    "data_context": {
      "kpis": [...],
      "insights": [...],
      "metrics": [...]
    }
  }'
```

**Response:**
```json
{
  "ok": true,
  "report": {
    "id": "rpt_abc123",
    "template_name": "executive_briefing",
    "report_type": "executive_briefing",
    "format": "html",
    "title": "Executive Briefing",
    "generated_at": "2026-06-17T10:00:00Z",
    "sections": [...]
  },
  "preview": "HTML content preview..."
}
```

### Export Formats

Supported formats:
- `html` - Browser-readable, interactive
- `pdf` - Print-friendly, portable
- `csv` - Spreadsheet-compatible
- `xlsx` - Excel workbook
- `json` - Machine-readable

---

## Scheduling Reports

### Create Schedule

Set up automatic report generation and delivery:

```bash
curl -X POST -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/reporting/schedules \
  -d '{
    "template_name": "executive_briefing",
    "frequency": "daily",
    "format": "pdf",
    "recipients": [
      "ceo@workcrew.ai",
      "cfo@workcrew.ai",
      "#leadership"
    ],
    "delivery_method": "both"
  }'
```

### Frequency Options

- `daily` - Every day at 8 AM
- `weekly` - Every Monday at 8 AM
- `monthly` - First day of month at 8 AM
- `quarterly` - First day of quarter at 8 AM
- `once` - Single delivery

### List Schedules

```bash
curl -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/reporting/schedules
```

### Enable/Disable Schedule

```bash
curl -X POST -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/reporting/schedules/{schedule_id}/disable
```

### Delete Schedule

```bash
curl -X DELETE -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/reporting/schedules/{schedule_id}
```

---

## Publishing Reports

### Publish to Recipients

Deliver generated report:

```bash
curl -X POST -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/reporting/publish \
  -d '{
    "report_id": "rpt_abc123",
    "recipients": [
      "user@example.com",
      "#sales-channel"
    ],
    "methods": ["email", "slack"],
    "html_content": "<html>...</html>"
  }'
```

**Response:**
```json
{
  "ok": true,
  "results": {
    "report_id": "rpt_abc123",
    "sent_count": 2,
    "failed_count": 0,
    "deliveries": [
      {
        "id": "dlv_1",
        "status": "sent",
        "recipient": "user@example.com",
        "method": "email"
      },
      {
        "id": "dlv_2",
        "status": "sent",
        "recipient": "#sales-channel",
        "method": "slack"
      }
    ]
  }
}
```

### Delivery Methods

**Email:**
- Recipient must be valid email address
- HTML/PDF attachment
- Custom subject line

**Slack:**
- Recipient must be channel (#channel)
- Preview message with link
- Formatted blocks

**Cloud Storage:**
- S3 bucket (requires config)
- Google Drive folder (requires config)
- Automatic naming and folder organization

---

## API Reference

### Templates

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/reporting/templates/register` | Register template |
| GET | `/api/v1/reporting/templates` | List templates |

### Report Generation

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/reporting/generate` | Generate report |

### Scheduling

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/reporting/schedules` | Create schedule |
| GET | `/api/v1/reporting/schedules` | List schedules |
| POST | `/api/v1/reporting/schedules/{id}/enable` | Enable schedule |
| POST | `/api/v1/reporting/schedules/{id}/disable` | Disable schedule |
| DELETE | `/api/v1/reporting/schedules/{id}` | Delete schedule |

### Publishing

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/reporting/publish` | Publish report |
| GET | `/api/v1/reporting/deliveries/{id}` | Get delivery status |

### Status

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v1/reporting/health` | System health |

---

## Use Cases

### Daily Executive Briefing

Setup:
```json
{
  "template_name": "executive_briefing",
  "frequency": "daily",
  "recipients": ["ceo@company.com", "cfo@company.com"],
  "delivery_method": "email",
  "format": "pdf"
}
```

Includes: Revenue, pipeline, risk alerts, insights

### Weekly Sales Pipeline Report

Setup:
```json
{
  "template_name": "sales_pipeline",
  "frequency": "weekly",
  "recipients": ["sales-team@company.com"],
  "delivery_method": "both",
  "format": "html"
}
```

Includes: Deals by stage, at-risk deals, win rate, coverage

### Monthly Customer Health Review

Setup:
```json
{
  "template_name": "customer_health",
  "frequency": "monthly",
  "recipients": ["csm-team@company.com", "#customer-success"],
  "delivery_method": "both",
  "format": "pdf"
}
```

Includes: Health scores, churn risks, expansion opportunities

### Quarterly Board Review

Setup:
```json
{
  "template_name": "monthly_review",
  "frequency": "quarterly",
  "recipients": ["board@company.com"],
  "delivery_method": "email",
  "format": "pdf"
}
```

Includes: Full metrics, trends, achievements, strategy

---

## Best Practices

### Template Design

- **Focus:** Each report solves one problem
- **Audience:** Know who reads each report
- **Length:** Executive = 2 pages, Detailed = 10 pages
- **Frequency:** Weekly max for execs, daily for operations

### Data Freshness

- Generate reports from live data (not cached)
- Cache results for 1 hour to avoid duplicate queries
- Manual refresh available on demand

### Delivery Timing

- Executive reports: 8 AM (ready for morning review)
- Sales reports: 9 AM (morning standup)
- CSM reports: 10 AM (after customer calls)
- Team summary: 5 PM (end of day digest)

### Format Selection

- **PDF**: Executive reports, board presentations, archival
- **HTML**: Interactive, quick review, web delivery
- **CSV/Excel**: Data analysis, trend comparison
- **JSON**: System integration, automation

### Distribution

- Email to individuals who need action
- Slack to teams for quick scanning
- Cloud storage for compliance/archival
- Direct URL for on-demand access

---

## Customization

### Custom Templates

Create custom templates for specific use cases:

```json
{
  "name": "custom_sales_report",
  "report_type": "custom",
  "title": "Weekly Sales Activity",
  "sections": [
    {
      "title": "Activity Metrics",
      "data_source": "metric",
      "parameters": {
        "metrics": ["calls", "emails", "meetings"],
        "group_by": "salesperson"
      }
    }
  ]
}
```

### Dynamic Parameters

Customize report at generation time:

```bash
curl -X POST ... -d '{
  "template_name": "sales_pipeline",
  "data_context": {
    "metrics": [...],
    "filter_stage": "PROPOSAL",
    "time_period": "30d"
  }
}'
```

### Conditional Sections

Include sections based on data:
- Skip sections with no data
- Show alerts only if threshold exceeded
- Highlight changes >10%

---

## Troubleshooting

### Report Generation Fails

**Check:**
- Template exists and is registered
- Data sources return valid data
- No malformed parameter values
- Sufficient system memory

### Delivery Issues

**Email:**
- SMTP configured
- Recipients in valid format
- Not hitting rate limits

**Slack:**
- Webhook URL valid
- Channel exists and bot has access
- Not exceeding Slack rate limits

### Missing Data

**Check:**
- Data context properly populated
- Time period filters correct
- Aggregation grouping valid
- Data source permissions

---

## Integration with Other Phases

### Hermes Integration
- Pipeline metrics automatically pulled
- Deal data in sales reports
- Win rate calculations

### Paperclip Integration
- KPIs as report sections
- Executive insights included
- Health scores referenced

### CSM Integration
- Account health data
- Churn risk predictions
- Expansion opportunities

### Forecasting Integration
- Revenue forecast in reports
- Scenario analysis results
- Model confidence metrics

### Integrations Phase
- Email delivery via SMTP
- Slack notifications
- Cloud storage upload (S3, Drive)
- Webhook triggers on completion

---

## Limitations

- Reports limited to 50 MB PDF
- Max 10,000 rows in table sections
- Export processing timeout: 5 minutes
- Scheduled reports limited to 20 per workspace
- Template sections limited to 50

---

## Future Enhancements

- Real-time report updates
- Custom report builder UI
- A/B testing for content
- Report analytics (open rates, clicks)
- Interactive dashboards
- Mobile app viewing
- Single sign-on for report links
- Custom branding (full white-label)
