# Deep Integrations (Phase 9)

## Overview

Phase 9 adds comprehensive **external integrations** to the AI Executive Operating System. Connect FounderOS with email, webhooks, calendar systems, and Slack for unified communications:

```
Email → SMS → Calendar → Slack → Webhooks → External Systems
```

---

## Email Integration

### Configuration

Set up SMTP for email delivery:

```bash
curl -X POST -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/integrations/email/configure \
  -d '{
    "host": "smtp.gmail.com",
    "port": 587,
    "use_tls": true,
    "username": "your-email@gmail.com",
    "password": "your-password",
    "from_email": "noreply@workcrew.ai"
  }'
```

### Email Templates

Create reusable email templates:

```bash
curl -X POST -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/integrations/email/templates \
  -d '{
    "name": "deal_closed",
    "subject": "Deal closed: {{deal_name}} - ${{deal_value}}",
    "html_body": "<h1>Congratulations!</h1><p>{{sales_rep_name}}, you closed {{deal_name}} for ${{deal_value}}!</p>",
    "text_body": "Congratulations! You closed {{deal_name}} for ${{deal_value}}!",
    "variables": ["deal_name", "deal_value", "sales_rep_name"]
  }'
```

### Send Email

#### Direct send:

```bash
curl -X POST -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/integrations/email/send \
  -d '{
    "to_email": "user@example.com",
    "subject": "Test Email",
    "html_body": "<h1>Hello</h1>",
    "cc": ["manager@example.com"],
    "bcc": ["archive@example.com"]
  }'
```

#### Using templates:

```bash
curl -X POST -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/integrations/email/template-send \
  -d '{
    "template_name": "deal_closed",
    "to_email": "sales@example.com",
    "context": {
      "deal_name": "Acme Corp",
      "deal_value": "50000",
      "sales_rep_name": "John Smith"
    }
  }'
```

### Scheduled Emails

Schedule email for future send:

```bash
curl -X POST -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/integrations/email/schedule \
  -d '{
    "template_name": "deal_closed",
    "to_email": "user@example.com",
    "context": {"deal_name": "Acme", "deal_value": "50000"},
    "send_at": "2026-07-01T09:00:00Z"
  }'
```

Process scheduled emails:

```bash
curl -X POST -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/integrations/email/process-scheduled
```

**Response:**
```json
{
  "ok": true,
  "sent": 5,
  "failed": 0,
  "total": 5
}
```

---

## Webhook Integration

### Create Subscription

Subscribe to FounderOS events:

```bash
curl -X POST -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/integrations/webhooks/subscribe \
  -d '{
    "url": "https://your-app.com/webhooks/workcrew",
    "events": [
      "deal.created",
      "deal.closed",
      "contact.scored",
      "account.at_risk"
    ],
    "metadata": {
      "source": "custom_crm",
      "environment": "production"
    }
  }'
```

**Response:**
```json
{
  "ok": true,
  "subscription": {
    "id": "sub_abc123",
    "url": "https://your-app.com/webhooks/workcrew",
    "events": ["deal.created", "deal.closed"],
    "active": true,
    "created_at": "2026-06-17T10:00:00Z",
    "failure_count": 0,
    "metadata": {...}
  }
}
```

### List Subscriptions

```bash
curl -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/integrations/webhooks/subscriptions
```

### Delete Subscription

```bash
curl -X DELETE -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/integrations/webhooks/subscriptions/{subscription_id}
```

### Webhook Events

Supported event types:

- `deal.created` - New deal created
- `deal.updated` - Deal information changed
- `deal.closed` - Deal marked as closed
- `contact.created` - New contact added
- `contact.updated` - Contact information changed
- `contact.scored` - Lead score calculated
- `account.health_changed` - Account health score updated
- `account.at_risk` - Account flagged at risk
- `forecast.updated` - Revenue forecast recalculated
- `churn.predicted` - Churn prediction generated

### Webhook Payload

All webhooks receive:

```json
{
  "event": "deal.created",
  "timestamp": "2026-06-17T10:30:00Z",
  "delivery_id": "dlv_xyz789",
  "data": {
    "deal_id": "deal_123",
    "deal_name": "Acme Corp",
    "deal_value": 50000,
    "stage": "PROPOSAL",
    "created_at": "2026-06-17T10:30:00Z"
  }
}
```

### Webhook Signature

Verify signature with HMAC-SHA256:

```python
import hmac
import hashlib
import json

def verify_webhook(request_body, header_signature, secret):
    body = json.dumps(json.loads(request_body), sort_keys=True)
    signature = hmac.new(
        secret.encode(),
        body.encode(),
        hashlib.sha256
    ).hexdigest()
    expected = f"sha256={signature}"
    return hmac.compare_digest(expected, header_signature)
```

Check headers:
- `X-Webhook-Signature` - HMAC signature
- `X-Webhook-ID` - Subscription ID
- `X-Delivery-ID` - Delivery attempt ID

### Delivery Retry

Webhooks retry up to 3 times with exponential backoff (2s, 4s, 8s).

---

## Slack Integration

### Configure

Set webhook URL:

```bash
curl -X POST -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/integrations/slack/configure \
  -d '{
    "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
  }'
```

### Send Message

```bash
curl -X POST -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/integrations/slack/send \
  -d '{
    "channel": "#sales",
    "text": "Deal closed!",
    "username": "WorkCrew Bot",
    "icon_emoji": ":chart_with_upwards_trend:"
  }'
```

### Send Alert

Color-coded alerts:

```bash
curl -X POST -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/integrations/slack/alert \
  -d '{
    "channel": "#leadership",
    "title": "Critical: Account At Risk",
    "message": "Acme Corp health score dropped to 25",
    "severity": "critical",
    "fields": {
      "Account": "Acme Corp",
      "Health Score": "25",
      "At Risk Days": "5"
    }
  }'
```

**Severity levels:**
- `info` (green, #36a64f)
- `warning` (orange, #ff9900)
- `critical` (red, #ff0000)

### Slash Commands

Predefined slash commands:

- `/workcrew-status` - System health & KPIs
- `/workcrew-pipeline` - Pipeline summary
- `/workcrew-risks` - At-risk deals
- `/workcrew-forecast` - Revenue forecast

---

## Calendar Integration

### Google Calendar

#### Configure:

```bash
curl -X POST -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/integrations/google-calendar/configure \
  -d '{
    "credentials": {
      "type": "service_account",
      "project_id": "your-project",
      "private_key_id": "key-id",
      "private_key": "-----BEGIN PRIVATE KEY-----...",
      "client_email": "service-account@project.iam.gserviceaccount.com",
      "client_id": "123456789",
      "auth_uri": "https://accounts.google.com/o/oauth2/auth",
      "token_uri": "https://oauth2.googleapis.com/token"
    }
  }'
```

#### Create Event:

```bash
curl -X POST -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/integrations/google-calendar/events \
  -d '{
    "title": "Sales Demo with Acme",
    "description": "Product demo for Acme Corp",
    "start_time": "2026-06-20T14:00:00Z",
    "end_time": "2026-06-20T15:00:00Z",
    "attendees": ["user@example.com", "customer@acme.com"],
    "location": "Google Meet"
  }'
```

### Outlook Calendar

#### Configure:

```bash
curl -X POST -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/integrations/outlook-calendar/configure \
  -d '{
    "tenant_id": "your-tenant-id",
    "access_token": "eyJhbGc..."
  }'
```

#### Create Event:

```bash
curl -X POST -H "Authorization: Bearer API_KEY" \
  https://api.workcrew.ai/api/v1/integrations/outlook-calendar/events \
  -d '{
    "title": "Customer Check-in",
    "description": "Monthly health check with customer",
    "start_time": "2026-06-20T10:00:00Z",
    "end_time": "2026-06-20T11:00:00Z",
    "attendees": ["user@example.com", "customer@example.com"]
  }'
```

---

## API Reference

### Email Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/integrations/email/configure` | Configure SMTP |
| POST | `/api/v1/integrations/email/templates` | Register template |
| POST | `/api/v1/integrations/email/send` | Send email |
| POST | `/api/v1/integrations/email/template-send` | Send from template |
| POST | `/api/v1/integrations/email/schedule` | Schedule email |
| POST | `/api/v1/integrations/email/process-scheduled` | Process queue |

### Webhook Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/integrations/webhooks/subscribe` | Create subscription |
| GET | `/api/v1/integrations/webhooks/subscriptions` | List subscriptions |
| DELETE | `/api/v1/integrations/webhooks/subscriptions/{id}` | Delete subscription |

### Slack Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/integrations/slack/configure` | Configure webhook |
| POST | `/api/v1/integrations/slack/send` | Send message |
| POST | `/api/v1/integrations/slack/alert` | Send alert |

### Calendar Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/integrations/google-calendar/configure` | Configure Google |
| POST | `/api/v1/integrations/google-calendar/events` | Create event |
| POST | `/api/v1/integrations/outlook-calendar/configure` | Configure Outlook |
| POST | `/api/v1/integrations/outlook-calendar/events` | Create event |

### Status

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v1/integrations/health` | Integration health |

---

## Use Cases

### Automated Deal Closure Notification

When deal closes, automatically:
1. Send congratulatory email to sales rep
2. Send notification to Slack
3. Create calendar event for customer success handoff
4. Trigger webhook to external CRM

### At-Risk Account Recovery

When account flagged at-risk:
1. Send alert to Slack #leadership
2. Email CSM with action items
3. Schedule follow-up meeting on calendar
4. Webhook to automation system

### Weekly Executive Briefing

Scheduled daily:
1. Generate forecast
2. Identify churn risks
3. Send Slack alert with summary
4. Email detailed report
5. Create calendar block for review

---

## Best Practices

### Email

- **Templates:** Create templates for consistent messaging
- **Scheduled:** Use scheduling for time-zone appropriate sends
- **Batch:** Send bulk emails through batch endpoint
- **Unsubscribe:** Include unsubscribe link in all emails

### Webhooks

- **Idempotency:** Handle duplicate deliveries gracefully
- **Timeouts:** Respond within 30 seconds
- **Retry:** Don't block webhook response on downstream calls
- **Signature:** Always verify HMAC signature

### Slack

- **Channels:** Use purpose-driven channels (#sales, #leadership)
- **Threads:** Keep related messages in threads
- **Limits:** Respect Slack rate limits (1 message/sec per channel)
- **Emoji:** Use emoji for visual scanning

### Calendar

- **Conflicts:** Check availability before creating
- **Timezones:** Always use UTC in API
- **Attendees:** Include all relevant participants
- **Reminders:** Set 24-hour reminder for important meetings

---

## Troubleshooting

### Email Not Sending

**Check:**
- SMTP credentials configured
- From address whitelisted
- Recipient not bouncing
- Logs for connection errors

### Webhooks Not Firing

**Check:**
- Subscription active (`active: true`)
- Event type matches (`events` array)
- Endpoint accessible (test with curl)
- Firewall allows outbound HTTPS

### Calendar Sync Issues

**Check:**
- Access token not expired
- Calendar ID correct
- Service account has permissions
- Attendee emails valid

---

## Security

### API Keys

- Store in environment variables
- Rotate quarterly
- Use separate keys per environment
- Never commit to git

### Webhook Signatures

- Verify HMAC-SHA256 signature
- Check timestamp within 5 minutes
- Fail silently on verification failure

### Calendar Access

- Use service accounts (not personal accounts)
- Grant minimal permissions
- Audit access regularly

---

## Limitations

- Email rate limited to 100/minute
- Webhooks retry 3 times only
- Calendar sync limited to 7 days
- Slack messages limited to 4000 characters
