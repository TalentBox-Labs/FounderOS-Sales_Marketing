# SaaS S0 — Frontend Decision

**Sprint:** SaaS S0  
**Date:** 2026-08-13  
**Mode:** AUDIT ONLY

## Jinja Shell Decision

**KEEP_JINJA_AND_MODERNIZE_INCREMENTALLY**

| Factor | Score (0–5) | Note |
|--------|------------:|------|
| Engineering risk | 5 | Lowest vs SPA remount |
| Contract risk | 5 | Preserves UI2.5 / OF1.5 / MDG1.5 surfaces |
| Time to usable SaaS | 4 | Identity wraps existing shell |
| UX limitations | 2 | Ops chrome, not polished SaaS |
| Future FE migration cost | 3 | Incremental |
| Backend coupling | 3 | Server-rendered composition |
| Testing impact | 4 | Existing freeze suites stay |

## SPA Decision

**DO_NOT_REMOUNT_AS_PRIMARY**

CRM SPA remains **RETAIN_AND_REFACTOR_LATER**. Remounting does not create SaaS and forks frozen Jinja authority surfaces.

## Selected option

**OPTION A — Keep Jinja and incrementally modernize** during SaaS foundation.

Reject OPTION B (mount SPA now) and OPTION C (replace FE before SaaS foundation).
