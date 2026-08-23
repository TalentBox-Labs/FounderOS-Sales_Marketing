# REV-ORCH M3 — Reply Classification Contract

Reply types (non-persistent structured object):

`INTERESTED` · `NEEDS_INFO` · `OBJECTION` · `NOT_NOW` · `NOT_INTERESTED` · `OPT_OUT` · `MEETING_INTEREST` · `UNKNOWN`

Objection categories: `PRICE` `TIMING` `AUTHORITY` `NEED` `COMPETITOR` `TRUST` `IMPLEMENTATION` `OTHER`

Confidence: 0–1. Below 0.4 routes to `UNKNOWN` / human review (except explicit `OPT_OUT`).

AI output is an input to `route_reply_assessment`. Invalid types become `UNKNOWN`.
