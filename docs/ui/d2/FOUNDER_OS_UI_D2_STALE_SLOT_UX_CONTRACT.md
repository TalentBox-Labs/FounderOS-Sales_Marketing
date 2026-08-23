# UI-D2 Stale Slot UX Contract

When M4.5 execution-time revalidation blocks a slot:

- Approval execution returns `executed: false` with stale/past reason
- UI must not auto-select another slot
- Contact workspace JS surfaces: "That time is no longer available. Please choose another slot."
- User may refresh availability via **View availability**

No bypass of provider revalidation. No silent fallback slots.
