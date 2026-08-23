# UI-D2 Error & Empty State Contract

| Condition | UI |
|-----------|-----|
| Not booking eligible | `booking-not-eligible` panel |
| No connector | `booking-no-connector` |
| Outlook only | `booking-outlook-unavailable` |
| No free slots | "No free slots found" |
| Provider read failure | Availability error message (no stack trace) |
| Approval pending | `booking-approval-pending` + inbox link |
| Rejected | Standard approval reject flow |
| Execution failed | Approval execution result / toast |
| Already booked | `booking-confirmation` |
| Missing optional meeting URL | Omitted (not invented) |

All states must render without template crash.
