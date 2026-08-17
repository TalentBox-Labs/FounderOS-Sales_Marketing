# REV-ORCH M3 — Reply Authority Matrix

| Actor | Persist inbound Activity | Classify | Route | Contact.status | Deal.stage | Accept QualifiedDemand | Book | Send |
|-------|--------------------------|----------|-------|----------------|------------|------------------------|------|------|
| n8n webhook | YES (transport) | NO | wake only | NO | NO | NO | NO | NO |
| ReplyAnalysisWorker | NO | YES | NO | NO | NO | NO | NO | NO |
| reply_routing | NO | NO | YES | tags OPT_OUT only | NO | NO | NO | NO |
| WorkflowOrchestrator | dispatch | NO | NO | NO | NO | NO | NO | NO |
| Human (session) | NO | NO | NO | YES (A4) | YES (A3) | YES (MC04.5) | future M4 | ApprovalRequest |
| Client payload org | NO | NO | NO | NO | NO | NO | NO | NO |
