# Founder OS International-Grade UI Requirements v1

**STATUS:** REQUIREMENTS ONLY — do not implement a design system in this sprint  
**Sprint:** COS-ARCH-v1  
**Baseline:** `a7463e5`

---

## 1. Current stack

- Jinja2 + `templates/base.html` + FastAPI `TemplateResponse`
- Server-rendered Founder loop; progressive JS on contact/approvals
- React `frontend/` unmounted unless `dist` present (Sales CRM RETAIN_AND_REFACTOR_LATER)
- English copy; emoji nav icons; timezone display exists on booking (M4.5 contract)

**Verdict: HYBRID**

| Option | Why not / why |
|--------|----------------|
| KEEP | Shell already ships UI-D1/D2; authority is server-side |
| EVOLVE | Tokens, type, a11y, i18n, density — in Jinja |
| HYBRID | **Chosen** — evolve Founder Jinja; leave Marketing engine pages; do not mount SPA as Founder shell |
| MIGRATE | Unjustified; would risk authority/tenant contracts and dual-app confusion |

Do not migrate frameworks for modernity.

---

## 2. Requirements (target, not current)

### Typography / spacing / density

- Scale: display / title / body / meta (meta already used as `founder-meta`)
- 8px spacing grid
- Home: low density; People lists: medium; Studio: high (isolated)

### Responsive

- Breakpoints: mobile sidebar (exists), tablet, desktop
- Booking slot list must work at 360px
- No hover-only Approve

### Accessibility

- **WCAG 2.2 AA** target
- Replace emoji-only nav with text + optional icon
- Focus visible on buttons/links
- `aria` on approval dialogs and live availability region
- Contrast on pills (blue/amber/green/red)

### i18n readiness

- No concatenated sentences in templates long-term; message ids
- Dates: ISO storage; display via org timezone (booking already timezone-aware)
- Currency: Deal values — store numeric; format by org locale (missing)
- Do not bake “Book meeting” only in English in authority logic

### Keyboard

- Tab order through primary actions
- Future command palette: Cmd/Ctrl+K — must not bind globally until implemented

### Patterns

| Pattern | Requirement |
|---------|-------------|
| Tables | Tenant-filtered; empty row, not fake numbers |
| Cards | One CTA; derived vs attested labeled |
| Charts | Analytics later; no chart library required for COS-1 |
| Forms | Server-validated; no client authority fields |
| Drawers/modals | Confirm approve/reject (exists); focus trap |
| Alerts | Fail closed copy; no fake success |
| Notifications | Count on Approvals; no parallel toast SoT |
| Status | Map to existing pills; don’t add “autonomous” |

### Mobile nav

- Primary 5 items max
- Domain nav in overflow

### Performance

- HTML TTFB: Founder pages query-scoped by org
- Availability fetch: explicit loading copy (exists)
- No unbounded log dumps on Home

### Design tokens

- CSS variables already in base theme (`data-theme="dark"`)
- Document tokens before adding a second CSS framework

---

## 3. Near-term vs later

| COS-1 | Later |
|-------|--------|
| Terminology + hierarchy in existing CSS | Full token package |
| AA focus on Founder 5 screens | Marketing engines |
| Timezone honest on meetings | Locale packs |
