# UI-D1.5 Browser Demo Contract v1.0

**STATUS: FROZEN**

## Browser Product Demonstration — YES

A human can, in a browser after login (and optional demo seed):

1. Land on Command Center
2. See demand and contacts
3. Open a contact workspace
4. Trigger governed research-to-outreach / follow-up propose (canonical APIs)
5. Approve or reject from Approval Inbox
6. Operate Demand → Deal → Outcome on Operator Flow
7. Inspect activity

Terminal/API knowledge is not required for that product path.

## Browser-Only External Reply Injection — NO

Inbound reply assessment (M3) is driven by n8n webhook or API simulation. There is no in-browser “inject reply” control. The workspace **displays** latest assessment when it exists.

Do not claim a fully browser-native acquisition → outbound → inbound reply generation loop.

## Differentiation

| Loop | Browser native? |
|------|-----------------|
| Login → attention → demand → contact → approval → operator | YES |
| Generate inbound email / n8n `email.replied` | NO |
