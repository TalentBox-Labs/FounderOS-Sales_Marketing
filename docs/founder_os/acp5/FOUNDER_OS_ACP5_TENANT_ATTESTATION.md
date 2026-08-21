# Founder OS ACP-5 — Tenant Attestation

**Baseline:** `founder-os-acp4-v1.0` @ `954af7b34590a45991dd098afb21235dfef71fd2`

## Guarantees (v1)

| Guarantee | Mechanism |
|-----------|-----------|
| Org-scoped loop items | `organization_id` on WorkItem, ApprovalRequest payload, AgentActionLog |
| Missing tenant fail closed | Propose/Command compose return empty/blocked; ACP-1/4 fence |
| Cross-tenant proposal blocked | `get_contact_for_tenant` / org mismatch skips; approval tenant binding |
| Approval same-org bind | payload.organization_id + `get_approval_for_tenant` on decide |
| Command org-only | `build_command_center_snapshot` / decision compose require org |
| No Contact-derived activation | Autonomous allowlist ∩ ACTIVE org only (ACP-1) |

## Follow-up play tenant path

1. Heartbeat resolves authorized orgs (`_resolve_orgs_or_block`)
2. Eligibility scan per org
3. Entity mismatch → skip + blocked provenance
4. Approval payload stamps `organization_id`
5. Decide requires tenant context + org-bound approval (ACP-4)

## Booking secondary (if included)

Same stamps and `get_contact_for_tenant` in `_run_booking_proposal`.

## Non-changes

Tenant model, membership, and activation policy are **unchanged** by ACP-5.
