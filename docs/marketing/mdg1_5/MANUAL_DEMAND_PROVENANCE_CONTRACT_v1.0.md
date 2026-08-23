# MANUAL DEMAND PROVENANCE CONTRACT v1.0

**STATUS: FROZEN**

## Truthful provenance always set

```json
{
  "registration_mode": "manual_founder_ui",
  "registration_surface": "/operator/demand/register",
  "manually_supplied": true
}
```

Optional `source_detail` appended only when the Founder typed it.

## Manually asserted source

`source` is a Founder-selected allowlist value (default `manual`).  
It is **not** a measured campaign/UTM conversion.

## Never manufactured

- utm_source / utm_medium / utm_campaign
- referrer
- automated channel analytics
- lead score
- conversion source pixels

Missing attribution remains missing (`consent=None`; no UTM keys).
