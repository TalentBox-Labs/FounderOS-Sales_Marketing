# N0 — Toolchain & Cost Analysis (Ledger)

**Sprint:** N0  
**Date:** 2026-08-10  
**Policy:** NO paid tools unless separately approved · **Do not install**  

---

## Per engine

| Engine | Already available | OSS / free options | External APIs | Likely future paid | Lock-in |
|--------|-------------------|--------------------|---------------|--------------------|---------|
| **SEO** | Website artifacts; SEO plans; manual `/api/v1/seo`; content quality keyword checks | Local HTML/checklist scoring; free GSC read later | Optional GSC / SERP | Paid SERP APIs if automated | Low if scoring stays local |
| **Social** | Publishing stubs; legacy `social_publisher` | Limited without platforms | LinkedIn/X/IG APIs | Ads boosts; higher API tiers | **High** per network |
| **Email** | SMTP notifier skeleton; nurture sketches | Self-hosted SMTP (poor deliverability) | ESP (SendGrid/Postmark/…) | **Likely** ESP for production | High on ESP |
| **Campaign** | Publishing job model | Internal orchestration only | Via Social/Email | Indirect via channels | Low alone |

---

## Paid tools required **now** for a first useful slice

| Engine | Paid required now? |
|--------|--------------------|
| SEO | **0** |
| Social | **0** cash, but **requires** platform developer accounts / API access |
| Email | **0** if toy SMTP; **production-grade** implies paid ESP later |
| Campaign | **0** (but useless without channels) |

**Ledger:** Prefer SEO first under Founder free/OSS policy.
