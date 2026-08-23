# S0 — Site Origin Contract

**Sprint:** S0  
**Agent:** NOVA  
**Status:** Contract defined · placeholder default active · production domain **pending ratification**

---

## 1. Authoritative origin contract

Conceptual:

```text
SITE_ORIGIN = https://<ratified-domain>
SITE_BASE   = SITE_ORIGIN + SITE_BASE_PATH   # default /blog
```

Implementation (follows existing env-var conventions, e.g. `SECRET_KEY`, `CLOUDFLARE_*`):

| Variable | Purpose | Default when unset |
|----------|---------|-------------------|
| `FOUNDER_SITE_ORIGIN` | Scheme + host (no path) | `https://example.invalid` |
| `FOUNDER_SITE_BASE_PATH` | Public path prefix | `/blog` |
| `FOUNDER_SITE_ORIGIN_RATIFIED` | Founder gate for production SEO | unset → not ratified |

Module: `src/tools/site_origin.py`

| Function | Returns |
|----------|---------|
| `get_configured_site_origin()` | Origin URL |
| `get_site_base()` | `{origin}{base_path}` |
| `is_site_origin_ratified()` | bool |
| `is_indexing_activation_allowed()` | bool (all gates) |

---

## 2. URL derivation rules

| URL type | Source |
|----------|--------|
| Page canonical | FM `canonical_url` **or** `{get_site_base()}/{slug}` |
| Sitemap `<loc>` | Feed item `link` (= page canonical at publish time) |
| RSS channel `<link>` | `get_site_base()` default |
| OpenGraph `og:url` | `build_metadata()` → page canonical |
| Schema.org `@id` / `url` | Same as canonical |

Changing `FOUNDER_SITE_ORIGIN` changes **generated** defaults only. Front-matter canonicals in existing bundles remain until content is updated (historical identity preserved).

---

## 3. Host reference audit (summary)

Full inventory from repository grep (Aug 2026). **Historical frozen docs are not rewritten.**

### 3.1 Runtime code

| Location | Host | Classification | S0 action |
|----------|------|----------------|-----------|
| `src/tools/site_origin.py` | `example.invalid` | PLACEHOLDER | ✅ authoritative default |
| `src/tools/website_engine/urls.py` | via `get_site_base()` | RUNTIME | ✅ abstracted |
| `src/tools/website_engine/feeds.py` | via `get_site_base()` | RUNTIME | ✅ abstracted |
| `src/tools/website_engine/metadata.py` | `site_name="WorkCrew"` | RUNTIME (brand label) | unchanged — not a domain |
| `src/tools/hashnode_publish.py` | `workcrew.ai` | RUNTIME (legacy channel) | out of Website scope; S1 may audit |
| `runner_api.py` | mixed refs | RUNTIME | not Website canonical path |
| `revenue_os/*`, `src/marketing_crew.py` | email/branding | RUNTIME (non-website) | not SEO origin |

### 3.2 Content bundles (historical)

| Location | Host | Classification |
|----------|------|----------------|
| `input/W*/05_Final.md` (14 files) | `workcrew.ai` | HISTORICAL — FM canonical |

### 3.3 Generated artifacts (point-in-time)

| Location | Host | Classification |
|----------|------|----------------|
| `output/website/**` | `workcrew.ai` | HISTORICAL — from FM at publish time |
| `output/website-deploy/**` | `workcrew.ai` | HISTORICAL — M6/M7 deployment snapshots |

### 3.4 Tests

| Location | Host | Classification |
|----------|------|----------------|
| `tests/test_website_engine.py` | FM uses `workcrew.ai` | TEST — explicit FM canonical |
| `tests/test_site_origin.py` | `example.invalid` | TEST — origin contract |
| `tests/test_static_provider.py` | FM canonical | TEST |

### 3.5 Documentation

| Location | Host | Classification |
|----------|------|----------------|
| `docs/operations/M7*.md`, `docs/marketing/M*.md`, `docs/governance/FDR_N05*.md` | both hosts | DOCUMENTATION / HISTORICAL — frozen |
| `docs/marketing/seo/S0_*.md` | reference only | DOCUMENTATION |

### 3.6 Infrastructure / deployment

| Host | Classification |
|------|----------------|
| `founderos-staging.pages.dev` | INFRASTRUCTURE — temporary public host |
| `preview.founderos-staging.pages.dev` | INFRASTRUCTURE — preview |
| `workcrew.ai` | DEPRECATED for future Founder OS production |

---

## 4. Governance alignment

| Domain | Status |
|--------|--------|
| `workcrew.ai` | **NOT authorized** for future Founder OS production canonical |
| `founderos-staging.pages.dev` | Temporary infrastructure only |
| Future production domain | **Pending Founder ratification** (FDR-N05 open) |

See `docs/governance/SEO_DOMAIN_DECISION_PENDING.md`.

---

## 5. Test strategy

Tests use `FOUNDER_SITE_ORIGIN=https://example.invalid` (RFC 2606 reserved TLD).

Proven behaviors (`tests/test_site_origin.py`):

- Default origin is placeholder when env unset
- Env change propagates to `build_canonical_url()` for slug-only builds
- FM canonical unchanged when origin changes
- RSS default channel link follows origin
- Indexing blocked without ratification

---

## 6. Verdict

**Origin Abstraction:** IMPLEMENTED — runtime defaults no longer hardcode `workcrew.ai`; configurable contract established.
