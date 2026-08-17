"""Editorial Approval Engine (Sprint E7) — human decisions + phase-scoped promote.

Founder Decisions (ratified):
  FDR-001 — Phase-scoped promote only
  FDR-002 — Human approval only (AI may recommend, never approve)
  FDR-003 — Editorial approval does NOT authorize publishing

Decisions are append-only under output/editorial_decisions/.
Approve may call promote_staged for a single phase; never publish/go-live.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from src.tools.promote_staged import promote_staged_bundle
from src.tools.promotion_audit import (
    PHASE2A_PROMOTION_FILENAMES,
    PHASE2B_PROMOTION_FILENAMES,
    PHASE3_PROMOTION_FILENAMES,
)
from src.tools.runtime_paths import REPO_ROOT

SCHEMA_VERSION = 1
DECISIONS_DIR = REPO_ROOT / "output" / "editorial_decisions"
HISTORY_JSONL = DECISIONS_DIR / "decisions.jsonl"

DECISION_APPROVE = "approve"
DECISION_REJECT = "reject"
DECISION_REQUEST_CHANGES = "request_changes"
VALID_DECISIONS = frozenset(
    {DECISION_APPROVE, DECISION_REJECT, DECISION_REQUEST_CHANGES}
)

VALID_PHASES = frozenset({"2a", "2b", "3"})

# Display states for the Editorial Approval Engine (decision layer; not tracker.csv).
STATE_DRAFT = "Draft"
STATE_REVIEW = "Review"
STATE_APPROVED = "Approved"
STATE_REJECTED = "Rejected"
STATE_NEEDS_CHANGES = "Needs Changes"
STATE_READY = "Ready"
EDITORIAL_STATES = (
    STATE_DRAFT,
    STATE_REVIEW,
    STATE_APPROVED,
    STATE_REJECTED,
    STATE_NEEDS_CHANGES,
    STATE_READY,
)

# Pending queue = awaiting human action (not successfully Approved for suggested phase).
PENDING_STATES = frozenset(
    {
        STATE_DRAFT,
        STATE_REVIEW,
        STATE_REJECTED,
        STATE_NEEDS_CHANGES,
        STATE_READY,
    }
)

# FDR-002 — reject non-human / automation identities (case-insensitive exact match).
_FORBIDDEN_APPROVER_NAMES = frozenset(
    {
        "ai",
        "agent",
        "bot",
        "automation",
        "crewai",
        "system",
        "openai",
        "llm",
        "gpt",
        "claude",
        "openclaw",
        "auto",
        "machine",
    }
)

_CONTENT_ID_RE = re.compile(r"^W\d{2}[A-Z]?$", re.IGNORECASE)

PHASE_FILES: dict[str, tuple[str, ...]] = {
    "2a": PHASE2A_PROMOTION_FILENAMES,
    "2b": PHASE2B_PROMOTION_FILENAMES,
    "3": PHASE3_PROMOTION_FILENAMES,
}


def decisions_dir() -> Path:
    return DECISIONS_DIR


def history_path() -> Path:
    return HISTORY_JSONL


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_content_id(content_id: str) -> str:
    cid = (content_id or "").strip().upper()
    if not _CONTENT_ID_RE.match(cid):
        raise ValueError(f"Invalid content_id: {content_id!r}")
    return cid


def normalize_phase(phase: str | None) -> str:
    p = (phase or "").strip().lower()
    if p not in VALID_PHASES:
        raise ValueError(f"Invalid phase (must be 2a|2b|3): {phase!r}")
    return p


def is_human_approver(approver: str) -> bool:
    """FDR-002: free-text human name required; block known automation identities."""
    name = (approver or "").strip()
    if not name or len(name) < 2:
        return False
    token = name.lower()
    if token in _FORBIDDEN_APPROVER_NAMES:
        return False
    # Block obvious machine-prefixed labels.
    if token.startswith("ai:") or token.startswith("agent:") or token.startswith("bot:"):
        return False
    return True


def _staging_candidates(content_id: str) -> list[str]:
    cid = content_id.upper()
    return [
        f"output/generated/{cid}",
        f"output/staging/{cid}",
        f"staging/{cid}",
    ]


def resolve_staging_root(content_id: str, *, phase: str | None = None) -> str | None:
    """Return first repo-relative staging dir that has the phase files (or any phase files)."""
    cid = content_id.upper()
    phases = [phase] if phase else ["2a", "2b", "3"]
    for rel in _staging_candidates(cid):
        root = REPO_ROOT / rel
        if not root.is_dir():
            continue
        for ph in phases:
            files = PHASE_FILES[ph]
            if all((root / name).is_file() for name in files):
                return rel
    # Fallback: directory exists and has any known promotion file.
    for rel in _staging_candidates(cid):
        root = REPO_ROOT / rel
        if not root.is_dir():
            continue
        for files in PHASE_FILES.values():
            if any((root / name).is_file() for name in files):
                return rel
    return None


def suggest_phase(artifacts: dict[str, Any], staging_root: str | None) -> str:
    """Infer phase-scoped promote target from existing artifacts + staging (no invention)."""
    draft = bool(artifacts.get("draft"))
    final = bool(artifacts.get("final"))
    checklist = bool(artifacts.get("checklist"))

    staging = REPO_ROOT / staging_root if staging_root else None
    if staging and staging.is_dir():
        if all((staging / n).is_file() for n in PHASE3_PROMOTION_FILENAMES) and not checklist:
            return "3"
        if all((staging / n).is_file() for n in PHASE2B_PROMOTION_FILENAMES) and not final:
            return "2b"
        if all((staging / n).is_file() for n in PHASE2A_PROMOTION_FILENAMES) and not draft:
            return "2a"
        if all((staging / n).is_file() for n in PHASE3_PROMOTION_FILENAMES):
            return "3"
        if all((staging / n).is_file() for n in PHASE2B_PROMOTION_FILENAMES):
            return "2b"
        if all((staging / n).is_file() for n in PHASE2A_PROMOTION_FILENAMES):
            return "2a"

    if not draft:
        return "2a"
    if not final:
        return "2b"
    return "3"


def load_all_decisions() -> list[dict[str, Any]]:
    path = history_path()
    if not path.is_file():
        return []
    out: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(rec, dict):
            out.append(rec)
    return out


def load_decisions_for(content_id: str) -> list[dict[str, Any]]:
    cid = content_id.upper()
    return [d for d in load_all_decisions() if str(d.get("content_id", "")).upper() == cid]


def latest_decision(
    content_id: str, *, phase: str | None = None
) -> dict[str, Any] | None:
    rows = load_decisions_for(content_id)
    if phase:
        rows = [r for r in rows if str(r.get("phase", "")).lower() == phase.lower()]
    if not rows:
        return None
    return rows[-1]


def successful_approve_for_phase(content_id: str, phase: str) -> dict[str, Any] | None:
    for rec in reversed(load_decisions_for(content_id)):
        if str(rec.get("phase", "")).lower() != phase.lower():
            continue
        if rec.get("decision") != DECISION_APPROVE:
            continue
        promo = rec.get("promotion") or {}
        if promo.get("ok") is True:
            return rec
        # approve without promotion block (should not happen) still counts if marked ok
    return None


def derive_editorial_state(
    *,
    artifacts: dict[str, Any],
    readiness_summary: str | None,
    validation_passed: bool | None,
    last: dict[str, Any] | None,
    phase: str,
) -> str:
    """Map evidence + last decision → Editorial Engine display state."""
    if last:
        decision = last.get("decision")
        last_phase = str(last.get("phase", "")).lower()
        if last_phase == phase.lower() or not phase:
            if decision == DECISION_REJECT:
                return STATE_REJECTED
            if decision == DECISION_REQUEST_CHANGES:
                return STATE_NEEDS_CHANGES
            if decision == DECISION_APPROVE:
                promo = last.get("promotion") or {}
                if promo.get("ok") is True:
                    return STATE_APPROVED
                # Failed promote leave item in Review for retry.
                return STATE_REVIEW

    draft = bool(artifacts.get("draft"))
    final = bool(artifacts.get("final"))

    if validation_passed is True and (
        readiness_summary == "all_default_reports_pass" or final or draft
    ):
        return STATE_READY

    if draft and not final:
        return STATE_DRAFT

    if readiness_summary == "has_failures":
        return STATE_REVIEW

    if draft or final:
        return STATE_REVIEW

    return STATE_DRAFT


def append_decision(record: dict[str, Any]) -> Path:
    """Append decision to JSONL and write latest snapshot. Never deletes history."""
    ddir = decisions_dir()
    ddir.mkdir(parents=True, exist_ok=True)
    path = history_path()
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")

    cid = str(record.get("content_id", "")).upper()
    phase = str(record.get("phase", ""))
    snap = ddir / f"{cid}_{phase}_latest.json"
    snap.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


PromoteFn = Callable[..., int]


def apply_decision(
    *,
    content_id: str,
    decision: str,
    approver: str,
    notes: str = "",
    phase: str | None = None,
    staging_root: str | None = None,
    artifacts: dict[str, Any] | None = None,
    readiness_summary: str | None = None,
    validation_passed: bool | None = None,
    promote_fn: PromoteFn | None = None,
    skip_validation: bool = False,
) -> dict[str, Any]:
    """
    Record a human editorial decision.

    approve → phase-scoped promote_staged (FDR-001); never publish (FDR-003).
    reject / request_changes → audit only; no promote.
    """
    cid = normalize_content_id(content_id)
    if decision not in VALID_DECISIONS:
        raise ValueError(f"Invalid decision: {decision!r}")

    if not is_human_approver(approver):
        raise PermissionError(
            "Human approver required (FDR-002). "
            "AI/automation identities cannot approve or decide."
        )

    arts = dict(artifacts or {})
    staging = staging_root or resolve_staging_root(cid)
    ph = normalize_phase(phase or suggest_phase(arts, staging))

    # Invalid / duplicate transitions
    if decision == DECISION_APPROVE:
        prior = successful_approve_for_phase(cid, ph)
        if prior is not None:
            raise LookupError(
                f"Duplicate approval: {cid} phase {ph} already approved "
                f"(decision_id={prior.get('decision_id')})"
            )
        if not staging:
            raise FileNotFoundError(
                f"No staging bundle found for {cid}; approve requires phase-scoped promote"
            )
        staging_path = REPO_ROOT / staging
        missing = [n for n in PHASE_FILES[ph] if not (staging_path / n).is_file()]
        if missing:
            raise FileNotFoundError(
                f"Staging incomplete for phase {ph}: missing {missing}"
            )

    # Invalid: reject/request-changes with empty decision already handled; allow supersede.

    promotion_meta: dict[str, Any] = {
        "attempted": False,
        "ok": None,
        "exit_code": None,
        "staging_root": staging,
        "publishes": False,  # FDR-003 explicit
    }

    if decision == DECISION_APPROVE:
        fn = promote_fn or promote_staged_bundle
        promotion_meta["attempted"] = True
        rc = fn(
            staging_root=staging,
            week_id=cid,
            phase=ph,
            skip_validation=skip_validation,
            dry_run=False,
            approver=approver.strip(),
            notes=notes or "",
        )
        promotion_meta["exit_code"] = rc
        promotion_meta["ok"] = rc == 0

    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "decision_id": str(uuid.uuid4()),
        "utc_timestamp": utc_now_iso(),
        "content_id": cid,
        "phase": ph,
        "bundle": staging or f"input/{cid}",
        "decision": decision,
        "approver": approver.strip(),
        "notes": notes or "",
        "promotion": promotion_meta,
        "authorizes_publish": False,  # FDR-003
    }
    append_decision(record)

    state = derive_editorial_state(
        artifacts=arts,
        readiness_summary=readiness_summary,
        validation_passed=validation_passed,
        last=record,
        phase=ph,
    )
    return {
        "ok": True if decision != DECISION_APPROVE else bool(promotion_meta.get("ok")),
        "editorial_state": state,
        "record": record,
    }


def build_item_view(
    *,
    content_id: str,
    title: str,
    artifacts: dict[str, Any],
    readiness: dict[str, Any] | None = None,
    tracker: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cid = normalize_content_id(content_id)
    staging = resolve_staging_root(cid)
    phase = suggest_phase(artifacts, staging)
    last = latest_decision(cid)  # latest across phases for display
    last_for_phase = latest_decision(cid, phase=phase) or last
    readiness = readiness or {}
    state = derive_editorial_state(
        artifacts=artifacts,
        readiness_summary=readiness.get("readiness_summary"),
        validation_passed=readiness.get("validation_passed"),
        last=last_for_phase,
        phase=phase,
    )
    history = load_decisions_for(cid)
    return {
        "content_id": cid,
        "title": title or "",
        "editorial_state": state,
        "phase": phase,
        "bundle": staging or f"input/{cid}",
        "staging_root": staging,
        "staging_available": bool(staging),
        "can_approve": (
            state != STATE_APPROVED
            and bool(staging)
            and successful_approve_for_phase(cid, phase) is None
        ),
        "authorizes_publish": False,
        "artifacts": artifacts,
        "tracker": tracker or {},
        "readiness": readiness,
        "latest_decision": last_for_phase,
        "audit": history,
        "content_studio_path": f"/content-studio/{cid}",
        "readiness_path": f"/api/v1/editorial/readiness/{cid}",
    }
