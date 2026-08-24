"""Command Center V2 — projection-only composition helper (I1).

Derives founder-visible presentation buckets and display adjacency from existing
Command / COS / ACP read-model data.

Does NOT:
- persist state or mint Situation IDs
- write to the database
- modify ApprovalRequest / AgentActionLog
- expand authority or execute effects
- invent join relationships
"""

from __future__ import annotations

from typing import Any

BUCKET_NEEDS_YOUR_JUDGMENT = "NEEDS_YOUR_JUDGMENT"
BUCKET_BLOCKED_OR_DEGRADED = "BLOCKED_OR_DEGRADED"
BUCKET_RUNNING_WITHOUT_YOU = "RUNNING_WITHOUT_YOU"
BUCKET_RECENTLY_CHANGED = "RECENTLY_CHANGED"

NEXT_HUMAN_DECISION_REQUIRED = "HUMAN_DECISION_REQUIRED"
NEXT_EXTERNAL_DEPENDENCY = "EXTERNAL_DEPENDENCY"
NEXT_NO_NEXT_ACTION = "NO_NEXT_ACTION"
NEXT_RECOMMENDED_FOUNDER_ACTION = "RECOMMENDED_FOUNDER_ACTION"
NEXT_SYSTEM_CONTINUES = "SYSTEM_CONTINUES"

_VISIBLE_STATE_RECOVERING = "RECOVERING"
_VISIBLE_STATE_BLOCKED = "BLOCKED"
_VISIBLE_STATE_WAITING_PROVIDER = "WAITING_ON_PROVIDER"
_VISIBLE_STATE_FAILED = "FAILED"
_VISIBLE_STATE_UNKNOWN = "UNKNOWN"
_VISIBLE_STATE_DECISION = "DECISION_REQUIRED"
_VISIBLE_STATE_RUNNING = "RUNNING"
_VISIBLE_STATE_COMPLETED = "COMPLETED"

# Orch key "active" is failed-oriented in compose_orchestration_summary — never
# treat it as healthy autonomous progress.
_ORCH_FAILED_ALIAS_KEY = "active"

_AUTONOMOUS_PROGRESS_STATES = frozenset(
    {
        "running",
        "in_progress",
        "proposed",
        "progressing",
        "retryable",
        "recovering",
    }
)


def _empty_projection(*, organization_id: str | None, reason: str) -> dict[str, Any]:
    return {
        "organization_id": organization_id,
        "source": "command_v2_projection",
        "persistent": False,
        "fail_closed_reason": reason,
        "buckets": {
            BUCKET_NEEDS_YOUR_JUDGMENT: [],
            BUCKET_BLOCKED_OR_DEGRADED: [],
            BUCKET_RUNNING_WITHOUT_YOU: [],
            BUCKET_RECENTLY_CHANGED: [],
        },
        "groups": [],
        "cards": [],
    }


def _norm_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _card(
    *,
    card_key: str,
    bucket: str,
    title: str,
    visible_state: str,
    organization_id: str,
    subject_kind: str | None = None,
    subject_id: str | None = None,
    kind: str | None = None,
    reason: str | None = None,
    next_move: str | None = None,
    proposed_action: str | None = None,
    provenance_action_type: str | None = None,
    occurred_at: str | None = None,
    href: str | None = None,
    source_identity: str | None = None,
    execution_mode: str | None = None,
) -> dict[str, Any]:
    return {
        "card_key": card_key,
        "bucket": bucket,
        "title": title,
        "visible_state": visible_state,
        "organization_id": organization_id,
        "subject_kind": subject_kind,
        "subject_id": subject_id,
        "kind": kind,
        "reason": reason,
        "next_move": next_move,
        "proposed_action": proposed_action,
        "provenance_action_type": provenance_action_type,
        "occurred_at": occurred_at,
        "href": href,
        "source_identity": source_identity,
        "execution_mode": execution_mode,
        # Presentation adjacency only — not a Situation ID / SoT.
        "presentation_subject_key": _presentation_subject_key(
            approval_request_id=subject_id if subject_kind == "approval_request" else None,
            demand_id=subject_id if subject_kind == "demand" else None,
            contact_id=subject_id if subject_kind == "contact" else None,
        ),
    }


def _presentation_subject_key(
    *,
    approval_request_id: str | None = None,
    demand_id: str | None = None,
    contact_id: str | None = None,
) -> str | None:
    """Deterministic display adjacency key. Not persisted. Not a Situation ID."""
    if approval_request_id:
        return f"approval_request:{approval_request_id}"
    if demand_id:
        return f"demand:{demand_id}"
    if contact_id:
        return f"contact:{contact_id}"
    return None


def _subject_from_decision_item(item: dict[str, Any]) -> tuple[str | None, str | None]:
    """Return (subject_kind, subject_id) using existing provenance / kind only."""
    kind = _norm_str(item.get("kind"))
    provenance = item.get("provenance") if isinstance(item.get("provenance"), dict) else {}
    subject = _norm_str(provenance.get("subject_id"))
    target = _norm_str(provenance.get("target_id"))

    if kind == "approval" and subject:
        return "approval_request", subject
    if kind == "qualified_demand" and subject:
        return "demand", subject
    if kind in ("meeting_interest", "follow_up") and subject:
        return "contact", subject
    if kind == "approval" and target:
        # Prefer approval id when present; target alone is contact adjacency only.
        return "contact", target
    if subject and kind == "outcome":
        return "contact", subject
    return None, None


def _dedupe_key_for_item(item: dict[str, Any], *, fallback_prefix: str) -> str:
    """Canonical presentation dedupe. ApprovalRequest.id wins over item_id."""
    provenance = item.get("provenance") if isinstance(item.get("provenance"), dict) else {}
    kind = _norm_str(item.get("kind"))
    if kind == "approval":
        approval_id = _norm_str(provenance.get("subject_id")) or _norm_str(item.get("id"))
        if approval_id:
            return f"approval:{approval_id}"
    if kind == "qualified_demand":
        demand_id = _norm_str(provenance.get("subject_id"))
        if demand_id:
            return f"demand:{demand_id}"
    item_id = _norm_str(item.get("item_id"))
    if item_id:
        return f"item:{item_id}"
    return f"{fallback_prefix}:{id(item)}"


def _mark_seen(seen: set[str], *keys: str | None) -> None:
    for key in keys:
        if key:
            seen.add(key)


def _next_move_for_decision(item: dict[str, Any], *, bucket: str) -> str | None:
    authority = _norm_str(item.get("authority_state"))
    proposed = _norm_str(item.get("proposed_action"))
    if bucket == BUCKET_NEEDS_YOUR_JUDGMENT or authority == "requires_founder":
        return NEXT_HUMAN_DECISION_REQUIRED
    if authority == "ready" and proposed:
        return NEXT_RECOMMENDED_FOUNDER_ACTION
    if authority == "completed":
        return NEXT_NO_NEXT_ACTION
    if proposed and authority == "informational":
        # Explicit recommendation text only — still not authority.
        return NEXT_RECOMMENDED_FOUNDER_ACTION
    return None


def _cards_from_decision_items(
    items: list[Any],
    *,
    organization_id: str,
    seen: set[str],
) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for raw in items:
        if not isinstance(raw, dict):
            continue
        authority = _norm_str(raw.get("authority_state"))
        kind = _norm_str(raw.get("kind"))
        dedupe = _dedupe_key_for_item(raw, fallback_prefix="decision")
        subject_kind, subject_id = _subject_from_decision_item(raw)

        # Pending ApprovalRequest / QD intake only for judgment.
        if authority == "requires_founder" and kind in ("approval", "qualified_demand"):
            if dedupe in seen:
                continue
            # Also fence alternate keys so pending_approvals cannot double-emit.
            alt_keys: list[str] = [dedupe]
            item_id = _norm_str(raw.get("item_id"))
            if item_id:
                alt_keys.append(f"item:{item_id}")
            if kind == "approval" and subject_id:
                alt_keys.append(f"approval:{subject_id}")
            if kind == "qualified_demand" and subject_id:
                alt_keys.append(f"demand:{subject_id}")
            if any(k in seen for k in alt_keys):
                continue
            _mark_seen(seen, *alt_keys)
            bucket = BUCKET_NEEDS_YOUR_JUDGMENT
            cards.append(
                _card(
                    card_key=dedupe,
                    bucket=bucket,
                    title=str(raw.get("title") or "Decision required"),
                    visible_state=_VISIBLE_STATE_DECISION,
                    organization_id=organization_id,
                    subject_kind=subject_kind,
                    subject_id=subject_id,
                    kind=kind,
                    reason=_norm_str(raw.get("reason")),
                    next_move=_next_move_for_decision(raw, bucket=bucket),
                    proposed_action=_norm_str(raw.get("proposed_action")),
                    provenance_action_type=_norm_str(
                        (raw.get("provenance") or {}).get("action_type")
                        if isinstance(raw.get("provenance"), dict)
                        else None
                    ),
                    occurred_at=_norm_str(raw.get("occurred_at")),
                    href=_norm_str(raw.get("href")),
                    source_identity=dedupe,
                )
            )
            continue

        # Completed band → recently changed.
        if authority == "completed":
            if dedupe in seen:
                continue
            seen.add(dedupe)
            bucket = BUCKET_RECENTLY_CHANGED
            cards.append(
                _card(
                    card_key=dedupe,
                    bucket=bucket,
                    title=str(raw.get("title") or "Completed"),
                    visible_state=_VISIBLE_STATE_COMPLETED,
                    organization_id=organization_id,
                    subject_kind=subject_kind,
                    subject_id=subject_id,
                    kind=kind,
                    reason=_norm_str(raw.get("reason")),
                    next_move=NEXT_NO_NEXT_ACTION,
                    proposed_action=_norm_str(raw.get("proposed_action")),
                    provenance_action_type=_norm_str(
                        (raw.get("provenance") or {}).get("action_type")
                        if isinstance(raw.get("provenance"), dict)
                        else None
                    ),
                    occurred_at=_norm_str(raw.get("occurred_at")),
                    href=_norm_str(raw.get("href")),
                    source_identity=dedupe,
                )
            )
            continue

        # Ready / informational recommendations are not judgment and not running.
        # They may surface as next-move only when I2 consumes proposed_action;
        # I1 does not invent a separate recommendation bucket.
    return cards


def _cards_from_pending_approvals(
    pending: list[Any],
    *,
    organization_id: str,
    seen: set[str],
) -> list[dict[str, Any]]:
    """Safety net: pending ApprovalRequest rows not yet in decision_items."""
    cards: list[dict[str, Any]] = []
    for raw in pending:
        if not isinstance(raw, dict):
            continue
        request_id = _norm_str(raw.get("id") or raw.get("request_id"))
        if not request_id:
            continue
        dedupe = f"approval:{request_id}"
        if dedupe in seen:
            continue
        seen.add(dedupe)
        target = _norm_str(raw.get("target_id"))
        cards.append(
            _card(
                card_key=dedupe,
                bucket=BUCKET_NEEDS_YOUR_JUDGMENT,
                title=str(raw.get("title") or raw.get("action_label") or "Approval request"),
                visible_state=_VISIBLE_STATE_DECISION,
                organization_id=organization_id,
                subject_kind="approval_request",
                subject_id=request_id,
                kind="approval",
                reason="An AI or system proposal is waiting. Nothing executes until you approve or reject.",
                next_move=NEXT_HUMAN_DECISION_REQUIRED,
                proposed_action=_norm_str(raw.get("action_label")),
                provenance_action_type=_norm_str(raw.get("action_type")),
                occurred_at=_norm_str(raw.get("created_at")),
                href=f"/contacts/{target}" if target else "/pending-approvals",
                source_identity=dedupe,
            )
        )
        # Contact adjacency is via presentation_subject_key on approval card only
        # when we also have contact — use approval id as primary subject (order rule).
        if target:
            # Keep approval_request primary; optional secondary meta only.
            cards[-1]["related_contact_id"] = target
    return cards


def _is_autonomous(item: dict[str, Any]) -> bool:
    mode = _norm_str(item.get("execution_mode"))
    return mode == "AUTONOMOUS" if mode else False


def _cards_from_orchestration(
    orch: dict[str, Any],
    *,
    organization_id: str,
    seen: set[str],
    pending_approval_ids: set[str],
) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []

    def _identity(item: dict[str, Any], prefix: str) -> str:
        wid = _norm_str(item.get("work_id"))
        if wid:
            return f"work:{wid}"
        at = _norm_str(item.get("action_type"))
        created = _norm_str(item.get("created_at"))
        return f"{prefix}:{at or 'work'}:{created or 'na'}"

    # Blocked / degraded
    for key, visible in (
        ("blocked", _VISIBLE_STATE_BLOCKED),
        ("exhausted", _VISIBLE_STATE_BLOCKED),
        ("ambiguous_effect", _VISIBLE_STATE_UNKNOWN),
        ("failed", _VISIBLE_STATE_FAILED),
    ):
        for raw in orch.get(key) or []:
            if not isinstance(raw, dict):
                continue
            # Failed items that are also retryable are handled as recovering below.
            if key == "failed":
                continue
            dedupe = _identity(raw, key)
            if dedupe in seen:
                continue
            seen.add(dedupe)
            contact = _norm_str(raw.get("contact_id") or raw.get("target_id"))
            cards.append(
                _card(
                    card_key=dedupe,
                    bucket=BUCKET_BLOCKED_OR_DEGRADED,
                    title=str(raw.get("work_kind") or raw.get("action_type") or "Blocked work"),
                    visible_state=visible,
                    organization_id=organization_id,
                    subject_kind="contact" if contact else None,
                    subject_id=contact,
                    kind="agent_orchestration",
                    reason=_norm_str(raw.get("failure_reason") or raw.get("escalation_reason")),
                    next_move=None,
                    occurred_at=_norm_str(raw.get("created_at")),
                    source_identity=dedupe,
                    execution_mode=_norm_str(raw.get("execution_mode")),
                )
            )

    # Failed without retry — blocked/degraded. Retryable handled separately.
    retryable_ids = {
        _identity(r, "retryable")
        for r in (orch.get("retryable") or [])
        if isinstance(r, dict)
    }
    for raw in orch.get("failed") or []:
        if not isinstance(raw, dict):
            continue
        dedupe = _identity(raw, "failed")
        # If same work also appears as retryable, prefer recovering classification.
        wid = _norm_str(raw.get("work_id"))
        retry_overlap = False
        if wid:
            for r in orch.get("retryable") or []:
                if isinstance(r, dict) and _norm_str(r.get("work_id")) == wid:
                    retry_overlap = True
                    break
        if retry_overlap or dedupe.replace("failed:", "retryable:") in retryable_ids:
            continue
        if dedupe in seen:
            continue
        seen.add(dedupe)
        contact = _norm_str(raw.get("contact_id") or raw.get("target_id"))
        cards.append(
            _card(
                card_key=dedupe,
                bucket=BUCKET_BLOCKED_OR_DEGRADED,
                title=str(raw.get("work_kind") or raw.get("action_type") or "Failed work"),
                visible_state=_VISIBLE_STATE_FAILED,
                organization_id=organization_id,
                subject_kind="contact" if contact else None,
                subject_id=contact,
                kind="agent_orchestration",
                reason=_norm_str(raw.get("failure_reason")),
                next_move=None,
                occurred_at=_norm_str(raw.get("created_at")),
                source_identity=dedupe,
                execution_mode=_norm_str(raw.get("execution_mode")),
            )
        )

    # Provider / connector degradation from pause or explicit provider flags
    pause = orch.get("pause") if isinstance(orch.get("pause"), dict) else {}
    if pause.get("acp2_execution_killed") or pause.get("heartbeat_paused"):
        dedupe = "runtime:degraded_gates"
        if dedupe not in seen:
            seen.add(dedupe)
            cards.append(
                _card(
                    card_key=dedupe,
                    bucket=BUCKET_BLOCKED_OR_DEGRADED,
                    title="Agent execution degraded",
                    visible_state=_VISIBLE_STATE_BLOCKED,
                    organization_id=organization_id,
                    kind="runtime_gate",
                    reason="Heartbeat paused or autonomous execution killed.",
                    next_move=None,
                    source_identity=dedupe,
                )
            )

    # Explicit provider-waiting list if present (booking connector etc. may inject)
    for raw in orch.get("waiting_on_provider") or []:
        if not isinstance(raw, dict):
            continue
        dedupe = _identity(raw, "provider")
        if dedupe in seen:
            continue
        seen.add(dedupe)
        cards.append(
            _card(
                card_key=dedupe,
                bucket=BUCKET_BLOCKED_OR_DEGRADED,
                title=str(raw.get("work_kind") or raw.get("title") or "Waiting on provider"),
                visible_state=_VISIBLE_STATE_WAITING_PROVIDER,
                organization_id=organization_id,
                kind="provider",
                reason=_norm_str(raw.get("reason") or raw.get("failure_reason")),
                next_move=NEXT_EXTERNAL_DEPENDENCY,
                occurred_at=_norm_str(raw.get("created_at")),
                source_identity=dedupe,
                execution_mode=_norm_str(raw.get("execution_mode")),
            )
        )

    # awaiting_human — NEVER Running without you; only note if not already a pending AR
    # (Needs judgment comes from ApprovalRequest / requires_founder, not orch alone.)
    for raw in orch.get("awaiting_human") or []:
        if not isinstance(raw, dict):
            continue
        # Explicitly do not add to RUNNING_WITHOUT_YOU.
        _ = raw

    # Recovering autonomous (retryable)
    for raw in orch.get("retryable") or []:
        if not isinstance(raw, dict):
            continue
        dedupe = _identity(raw, "retryable")
        if dedupe in seen:
            continue
        # Exclude if this work is pending ApprovalRequest subject (when linked)
        subject_ar = _norm_str(raw.get("approval_request_id"))
        if subject_ar and subject_ar in pending_approval_ids:
            continue
        seen.add(dedupe)
        contact = _norm_str(raw.get("contact_id") or raw.get("target_id"))
        # Prefer autonomous; if mode missing, still allow retryable as recovering progress.
        mode = _norm_str(raw.get("execution_mode"))
        if mode and mode != "AUTONOMOUS":
            # HUMAN_REQUIRED retryable waiting should not be "running without you"
            if mode == "HUMAN_REQUIRED":
                continue
        cards.append(
            _card(
                card_key=dedupe,
                bucket=BUCKET_RUNNING_WITHOUT_YOU,
                title=str(raw.get("work_kind") or raw.get("action_type") or "Recovering work"),
                visible_state=_VISIBLE_STATE_RECOVERING,
                organization_id=organization_id,
                subject_kind="contact" if contact else None,
                subject_id=contact,
                kind="agent_orchestration",
                reason=_norm_str(raw.get("failure_reason") or raw.get("recovery_class")),
                next_move=NEXT_SYSTEM_CONTINUES
                if (not mode or mode == "AUTONOMOUS")
                and (
                    pause.get("recovery_execution_allowed")
                    or pause.get("new_mutating_work_allowed") is not False
                )
                else None,
                occurred_at=_norm_str(raw.get("created_at")),
                source_identity=dedupe,
                execution_mode=mode or "AUTONOMOUS",
            )
        )

    # Active autonomous progress — optional lists only; NEVER orch["active"] (failed alias)
    for list_key in ("running", "in_progress", "autonomous_running"):
        for raw in orch.get(list_key) or []:
            if not isinstance(raw, dict):
                continue
            if not _is_autonomous(raw):
                # Allow missing mode only when state clearly progressing
                state = (_norm_str(raw.get("state")) or "").lower()
                if state not in _AUTONOMOUS_PROGRESS_STATES:
                    continue
            dedupe = _identity(raw, list_key)
            if dedupe in seen:
                continue
            subject_ar = _norm_str(raw.get("approval_request_id"))
            if subject_ar and subject_ar in pending_approval_ids:
                continue
            seen.add(dedupe)
            contact = _norm_str(raw.get("contact_id") or raw.get("target_id"))
            state = (_norm_str(raw.get("state")) or "running").lower()
            visible = (
                _VISIBLE_STATE_RECOVERING
                if state in {"retryable", "recovering"}
                else _VISIBLE_STATE_RUNNING
            )
            cards.append(
                _card(
                    card_key=dedupe,
                    bucket=BUCKET_RUNNING_WITHOUT_YOU,
                    title=str(raw.get("work_kind") or raw.get("action_type") or "Agent work"),
                    visible_state=visible,
                    organization_id=organization_id,
                    subject_kind="contact" if contact else None,
                    subject_id=contact,
                    kind="agent_orchestration",
                    reason=_norm_str(raw.get("escalation_reason")),
                    next_move=NEXT_SYSTEM_CONTINUES
                    if visible == _VISIBLE_STATE_RUNNING
                    else (
                        NEXT_SYSTEM_CONTINUES
                        if pause.get("recovery_execution_allowed") is not False
                        else None
                    ),
                    occurred_at=_norm_str(raw.get("created_at")),
                    source_identity=dedupe,
                    execution_mode=_norm_str(raw.get("execution_mode")) or "AUTONOMOUS",
                )
            )

    # Intentionally ignore orch[_ORCH_FAILED_ALIAS_KEY] for Running without you.
    _ = orch.get(_ORCH_FAILED_ALIAS_KEY)

    # Recently succeeded
    for raw in orch.get("succeeded_recently") or []:
        if not isinstance(raw, dict):
            continue
        dedupe = _identity(raw, "succeeded")
        if dedupe in seen:
            continue
        seen.add(dedupe)
        contact = _norm_str(raw.get("contact_id") or raw.get("target_id"))
        cards.append(
            _card(
                card_key=dedupe,
                bucket=BUCKET_RECENTLY_CHANGED,
                title=str(raw.get("work_kind") or raw.get("action_type") or "Completed work"),
                visible_state=_VISIBLE_STATE_COMPLETED,
                organization_id=organization_id,
                subject_kind="contact" if contact else None,
                subject_id=contact,
                kind="agent_orchestration",
                next_move=NEXT_NO_NEXT_ACTION,
                occurred_at=_norm_str(raw.get("created_at")),
                source_identity=dedupe,
                execution_mode=_norm_str(raw.get("execution_mode")),
            )
        )

    return cards


def _cards_from_recent_activity(
    activity: list[Any],
    *,
    organization_id: str,
    seen: set[str],
) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for raw in activity:
        if not isinstance(raw, dict):
            continue
        aid = _norm_str(raw.get("id") or raw.get("activity_id"))
        label = _norm_str(raw.get("label") or raw.get("action_type"))
        created = _norm_str(raw.get("created_at"))
        dedupe = f"activity:{aid}" if aid else f"activity:{label}:{created}"
        if dedupe in seen:
            continue
        seen.add(dedupe)
        contact = _norm_str(raw.get("contact_id") or raw.get("target_id"))
        cards.append(
            _card(
                card_key=dedupe,
                bucket=BUCKET_RECENTLY_CHANGED,
                title=str(label or "Recent activity"),
                visible_state=_VISIBLE_STATE_COMPLETED,
                organization_id=organization_id,
                subject_kind="contact" if contact else None,
                subject_id=contact,
                kind="activity",
                next_move=NEXT_NO_NEXT_ACTION,
                provenance_action_type=_norm_str(raw.get("action_type")),
                occurred_at=created,
                source_identity=dedupe,
            )
        )
    return cards


def _cards_from_booking_signals(
    meeting_interest: list[Any],
    *,
    organization_id: str,
    snapshot_errors: list[Any],
    seen: set[str],
) -> list[dict[str, Any]]:
    """Eligibility and connector degradation — never invent pending ApprovalRequest."""
    cards: list[dict[str, Any]] = []
    # Connector / snapshot degradation
    for err in snapshot_errors or []:
        token = str(err).lower()
        if token in {"database", "agent_orchestration", "approvals", "operator_flow"}:
            dedupe = f"error:{token}"
            if dedupe in seen:
                continue
            seen.add(dedupe)
            cards.append(
                _card(
                    card_key=dedupe,
                    bucket=BUCKET_BLOCKED_OR_DEGRADED,
                    title="Command data degraded",
                    visible_state=_VISIBLE_STATE_BLOCKED,
                    organization_id=organization_id,
                    kind="snapshot_error",
                    reason=f"Read path unavailable: {token}",
                    next_move=None,
                    source_identity=dedupe,
                )
            )

    for raw in meeting_interest or []:
        if not isinstance(raw, dict):
            continue
        # Explicit connector unavailable markers if present on rows
        ui_state = _norm_str(raw.get("ui_state") or raw.get("booking_status"))
        contact = _norm_str(raw.get("contact_id"))
        if ui_state in {"NO_CONNECTOR", "CONNECTOR_UNAVAILABLE"}:
            dedupe = f"booking_provider:{contact or 'org'}"
            if dedupe in seen:
                continue
            seen.add(dedupe)
            cards.append(
                _card(
                    card_key=dedupe,
                    bucket=BUCKET_BLOCKED_OR_DEGRADED,
                    title="Calendar provider unavailable",
                    visible_state=_VISIBLE_STATE_WAITING_PROVIDER,
                    organization_id=organization_id,
                    subject_kind="contact" if contact else None,
                    subject_id=contact,
                    kind="booking",
                    reason=_norm_str(raw.get("message") or raw.get("reason")),
                    next_move=NEXT_EXTERNAL_DEPENDENCY,
                    source_identity=dedupe,
                )
            )
        # eligible / interest alone → NOT needs judgment, NOT pending
    return cards


def _group_cards(cards: list[dict[str, Any]], *, organization_id: str) -> list[dict[str, Any]]:
    """Display adjacency only. Never cross organization_id. No Situation ID."""
    groups: dict[str, dict[str, Any]] = {}
    singletons: list[dict[str, Any]] = []

    for card in cards:
        if _norm_str(card.get("organization_id")) != organization_id:
            # Tenant fence — drop foreign org cards entirely.
            continue
        key = _norm_str(card.get("presentation_subject_key"))
        if not key:
            singletons.append(
                {
                    "presentation_subject_key": None,
                    "organization_id": organization_id,
                    "card_keys": [card["card_key"]],
                    "singleton": True,
                }
            )
            continue
        group = groups.get(key)
        if group is None:
            group = {
                "presentation_subject_key": key,
                "organization_id": organization_id,
                "card_keys": [],
                "singleton": False,
            }
            groups[key] = group
        group["card_keys"].append(card["card_key"])

    ordered = list(groups.values()) + singletons
    # Deterministic order by subject key then singleton order
    ordered.sort(
        key=lambda g: (
            0 if not g.get("singleton") else 1,
            str(g.get("presentation_subject_key") or ""),
            ",".join(g.get("card_keys") or []),
        )
    )
    return ordered


def compose_command_v2_projection(
    snapshot: Any,
    *,
    organization_id: str | None,
) -> dict[str, Any]:
    """Compose presentation-only Command V2 buckets from an existing snapshot.

    Pure function: no DB access, no writes, no authority.
    """
    org = _norm_str(organization_id)
    if not org:
        return _empty_projection(organization_id=None, reason="missing_organization_id")

    if not isinstance(snapshot, dict):
        return _empty_projection(organization_id=org, reason="invalid_snapshot")

    # Fail closed: never join using a mismatched org stamp on the snapshot if present.
    snap_org = _norm_str(snapshot.get("organization_id"))
    if snap_org and snap_org != org:
        return _empty_projection(organization_id=org, reason="organization_mismatch")

    decision_items = snapshot.get("decision_items")
    if not isinstance(decision_items, list):
        decision_items = []
    pending_approvals = snapshot.get("pending_approvals")
    if not isinstance(pending_approvals, list):
        pending_approvals = []
    orch = snapshot.get("agent_orchestration")
    if not isinstance(orch, dict):
        orch = {}
    recent_activity = snapshot.get("recent_activity")
    if not isinstance(recent_activity, list):
        recent_activity = []
    meeting_interest = snapshot.get("meeting_interest")
    if not isinstance(meeting_interest, list):
        meeting_interest = []
    errors = snapshot.get("errors")
    if not isinstance(errors, list):
        errors = []

    pending_approval_ids: set[str] = set()
    for row in pending_approvals:
        if isinstance(row, dict):
            rid = _norm_str(row.get("id") or row.get("request_id"))
            if rid:
                pending_approval_ids.add(rid)
    for item in decision_items:
        if not isinstance(item, dict):
            continue
        if _norm_str(item.get("kind")) == "approval" and _norm_str(item.get("authority_state")) == "requires_founder":
            prov = item.get("provenance") if isinstance(item.get("provenance"), dict) else {}
            rid = _norm_str(prov.get("subject_id"))
            if rid:
                pending_approval_ids.add(rid)

    seen: set[str] = set()
    cards: list[dict[str, Any]] = []
    cards.extend(_cards_from_decision_items(decision_items, organization_id=org, seen=seen))
    cards.extend(
        _cards_from_pending_approvals(pending_approvals, organization_id=org, seen=seen)
    )
    cards.extend(
        _cards_from_orchestration(
            orch,
            organization_id=org,
            seen=seen,
            pending_approval_ids=pending_approval_ids,
        )
    )
    cards.extend(
        _cards_from_recent_activity(recent_activity, organization_id=org, seen=seen)
    )
    cards.extend(
        _cards_from_booking_signals(
            meeting_interest,
            organization_id=org,
            snapshot_errors=errors,
            seen=seen,
        )
    )

    by_bucket: dict[str, list[dict[str, Any]]] = {
        BUCKET_NEEDS_YOUR_JUDGMENT: [],
        BUCKET_BLOCKED_OR_DEGRADED: [],
        BUCKET_RUNNING_WITHOUT_YOU: [],
        BUCKET_RECENTLY_CHANGED: [],
    }
    for card in cards:
        bucket = str(card.get("bucket") or "")
        if bucket in by_bucket:
            by_bucket[bucket].append(card)
    for bucket, items in by_bucket.items():
        with_ts = [c for c in items if c.get("occurred_at")]
        without_ts = [c for c in items if not c.get("occurred_at")]
        with_ts.sort(key=lambda c: str(c.get("occurred_at")), reverse=True)
        without_ts.sort(key=lambda c: str(c.get("card_key") or ""))
        by_bucket[bucket] = with_ts + without_ts

    flat: list[dict[str, Any]] = []
    for bucket in (
        BUCKET_NEEDS_YOUR_JUDGMENT,
        BUCKET_BLOCKED_OR_DEGRADED,
        BUCKET_RUNNING_WITHOUT_YOU,
        BUCKET_RECENTLY_CHANGED,
    ):
        flat.extend(by_bucket[bucket])

    groups = _group_cards(flat, organization_id=org)

    return {
        "organization_id": org,
        "source": "command_v2_projection",
        "persistent": False,
        "fail_closed_reason": None,
        "buckets": by_bucket,
        "groups": groups,
        "cards": flat,
    }
