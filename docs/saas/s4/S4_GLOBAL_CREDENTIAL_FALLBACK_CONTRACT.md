# S4 — Global Credential Fallback Contract

**Blocked:** Org B tenant request falling back to Org A or global credential when `allow_global_fallback=False`.

**Allowed:** `hydrate_all_connectors()` loads NULL-org rows for process startup (GLOBAL_BY_DESIGN).

**Blocked:** Tenant CRM enrich using global Proxycurl key when org-specific key exists separately — org key required when tenant resolves.
