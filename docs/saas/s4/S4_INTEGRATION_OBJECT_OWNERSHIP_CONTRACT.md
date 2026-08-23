# S4 — Integration Object Ownership Contract

After org resolution, `scoped_contact` / tenant guards validate object belongs to org.

Cross-tenant `contact_id` → 404 when org binding active.

Deal/other IDs: same pattern when handlers mutate tenant objects.
