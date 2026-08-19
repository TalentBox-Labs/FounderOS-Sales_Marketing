# Founder OS COS-1 Regression Reconciliation

| Envelope | Result |
|----------|--------|
| COS-1 focused | See test run |
| UI-D2 22 + compat 8 | Must remain green |
| D1.x init_db / metrics / founder company seed | Must remain green |
| UI-D1.5 nav + demo seed contract | Must remain green |
| Frozen D1 absence booking tests | SUPERSEDED_NEGATIVE_SCOPE — untouched, expected fail historically |

No frozen test files modified.

INT-D2 activity still receives `action_type` strings in HTML (`data-testid="activity-event-type"`).
