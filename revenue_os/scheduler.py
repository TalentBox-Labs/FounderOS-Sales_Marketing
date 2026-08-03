"""Heartbeat scheduler — recurring autonomous jobs, no external broker needed.

Runs inside the FastAPI process via asyncio, so it works identically on a
laptop (SQLite, `uvicorn runner_api:app`) and in production. Each job run is
persisted to `heartbeat_runs` and every action taken is written to the
`agent_action_log` audit trail.

Configuration (environment variables):
    HEARTBEAT_ENABLED=1|0            master switch (default 1)
    HEARTBEAT_LEAD_SCORING_SEC       default 3600  (hourly)
    HEARTBEAT_DEAL_RISK_SEC          default 21600 (every 6 hours)
    HEARTBEAT_METRICS_SNAPSHOT_SEC   default 3600  (hourly)
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from revenue_os.database import SessionLocal
from revenue_os.models.automation_state import HeartbeatRun
from revenue_os.services.activity_log import log_agent_action

logger = logging.getLogger(__name__)

ACTOR = "heartbeat"


# ── Job implementations ──────────────────────────────────────────────────────


def job_score_new_leads() -> dict[str, Any]:
    """Score contacts that have no lead score yet (up to 25 per run)."""
    from revenue_os.models.contact import Contact
    from revenue_os.services.lead_scoring_service import score_contact

    db = SessionLocal()
    try:
        contacts = (
            db.query(Contact)
            .filter((Contact.lead_score == None) | (Contact.lead_score == 0))  # noqa: E711
            .limit(25)
            .all()
        )
        scored = 0
        for contact in contacts:
            try:
                score = score_contact(db, contact)
                scored += 1
                log_agent_action(
                    actor=ACTOR,
                    action_type="lead_scored",
                    target_type="contact",
                    target_id=str(contact.id),
                    detail={"score": score},
                )
            except Exception as e:
                logger.warning(f"Scoring failed for contact {contact.id}: {e}")
        db.commit()
        return {"contacts_considered": len(contacts), "contacts_scored": scored}
    finally:
        db.close()


def job_check_deals_at_risk() -> dict[str, Any]:
    """Detect at-risk deals and emit events so workflows can react."""
    from revenue_os.automation.events import emit_deal_at_risk
    from revenue_os.services.deal_automation_service import get_deals_at_risk

    db = SessionLocal()
    try:
        at_risk = get_deals_at_risk(db)
        for deal in at_risk:
            deal_id = str(deal.get("deal_id") or deal.get("id") or "")
            try:
                emit_deal_at_risk(
                    deal_id=deal_id,
                    risk_score=int(deal.get("risk_score", 0)),
                    days_overdue=int(deal.get("days_overdue", 0)),
                )
            except Exception as e:
                logger.warning(f"emit_deal_at_risk failed for {deal_id}: {e}")
            log_agent_action(
                actor=ACTOR,
                action_type="deal_at_risk_flagged",
                target_type="deal",
                target_id=deal_id,
                detail=deal,
            )
        return {"deals_at_risk": len(at_risk)}
    finally:
        db.close()


def job_snapshot_pipeline_metrics() -> dict[str, Any]:
    """Persist a pipeline-health snapshot as analytics data points."""
    from revenue_os.analytics.core import AnalyticsEngine, AnalyticsMetric, MetricType
    from revenue_os.services.deal_automation_service import get_pipeline_health

    db = SessionLocal()
    try:
        health = get_pipeline_health(db)
    finally:
        db.close()

    snapshot_metrics = {
        "pipeline_total_value": (
            MetricType.REVENUE, "$", "Total open pipeline value",
            float(health.get("total_pipeline_value", 0) or 0),
        ),
        "pipeline_deal_count": (
            MetricType.COUNT, "deals", "Number of open deals",
            float(health.get("total_deals", 0) or 0),
        ),
        "pipeline_weighted_forecast": (
            MetricType.REVENUE, "$", "Probability-weighted forecast",
            float(health.get("weighted_forecast", 0) or 0),
        ),
    }

    recorded = {}
    for metric_id, (mtype, unit, description, value) in snapshot_metrics.items():
        if AnalyticsEngine.get_metric(metric_id) is None:
            AnalyticsEngine.register_metric(AnalyticsMetric(
                id=metric_id,
                name=metric_id.replace("_", " ").title(),
                metric_type=mtype,
                calculation="heartbeat snapshot",
                unit=unit,
                description=description,
            ))
        AnalyticsEngine.record_data_point(metric_id, value, dimension="snapshot")
        recorded[metric_id] = value

    log_agent_action(
        actor=ACTOR,
        action_type="metrics_snapshot",
        target_type="pipeline",
        detail=recorded,
    )
    return recorded


# ── Scheduler core ───────────────────────────────────────────────────────────


@dataclass
class HeartbeatJob:
    name: str
    func: Callable[[], dict[str, Any]]
    interval_seconds: int
    last_run_at: datetime | None = None
    last_status: str | None = None
    runs: int = 0


class HeartbeatScheduler:
    """Asyncio-based recurring job runner with persisted run history."""

    def __init__(self) -> None:
        self.jobs: dict[str, HeartbeatJob] = {}
        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()

    def register(self, name: str, func: Callable[[], dict[str, Any]], interval_seconds: int) -> None:
        self.jobs[name] = HeartbeatJob(name=name, func=func, interval_seconds=interval_seconds)

    def run_job_now(self, name: str) -> dict[str, Any]:
        """Execute one job synchronously, recording the run. Raises KeyError if unknown."""
        job = self.jobs[name]
        db = SessionLocal()
        run = HeartbeatRun(job_name=name, status="running")
        try:
            db.add(run)
            db.commit()
            db.refresh(run)
        except Exception as e:
            logger.warning(f"Could not persist heartbeat run start: {e}")
        finally:
            db.close()

        job.last_run_at = datetime.now(timezone.utc)
        job.runs += 1
        try:
            result = job.func() or {}
            job.last_status = "completed"
            self._finish_run(run.id, "completed", result=result)
            logger.info(f"Heartbeat job completed: {name} -> {result}")
            return {"job": name, "status": "completed", "result": result}
        except Exception as e:
            job.last_status = "failed"
            self._finish_run(run.id, "failed", error=str(e))
            logger.error(f"Heartbeat job failed: {name}: {e}")
            return {"job": name, "status": "failed", "error": str(e)}

    @staticmethod
    def _finish_run(run_id: str, status: str, result: dict | None = None, error: str | None = None) -> None:
        try:
            db = SessionLocal()
            try:
                run = db.get(HeartbeatRun, run_id)
                if run is not None:
                    run.status = status
                    run.finished_at = datetime.now(timezone.utc)
                    run.result = result
                    run.error = error
                    db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Could not persist heartbeat run finish: {e}")

    async def _loop(self) -> None:
        logger.info(f"Heartbeat started with {len(self.jobs)} jobs: {list(self.jobs)}")
        # Stagger: wait a moment after boot before the first pass.
        await asyncio.sleep(10)
        while not self._stop.is_set():
            now = datetime.now(timezone.utc)
            for job in self.jobs.values():
                due = (
                    job.last_run_at is None
                    or (now - job.last_run_at).total_seconds() >= job.interval_seconds
                )
                if due:
                    await asyncio.to_thread(self.run_job_now, job.name)
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=30)
            except asyncio.TimeoutError:
                pass
        logger.info("Heartbeat stopped")

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._stop.clear()
            self._task = asyncio.get_event_loop().create_task(self._loop())

    def stop(self) -> None:
        self._stop.set()

    def status(self) -> dict[str, Any]:
        return {
            "enabled": True,
            "running": self._task is not None and not self._task.done(),
            "jobs": [
                {
                    "name": j.name,
                    "interval_seconds": j.interval_seconds,
                    "last_run_at": j.last_run_at.isoformat() if j.last_run_at else None,
                    "last_status": j.last_status,
                    "runs": j.runs,
                }
                for j in self.jobs.values()
            ],
        }


scheduler = HeartbeatScheduler()


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


def heartbeat_enabled() -> bool:
    return os.environ.get("HEARTBEAT_ENABLED", "1") not in ("0", "false", "False")


def initialize_heartbeat() -> HeartbeatScheduler:
    """Register default jobs and start the loop (call from app startup)."""
    scheduler.register(
        "score_new_leads", job_score_new_leads,
        _env_int("HEARTBEAT_LEAD_SCORING_SEC", 3600),
    )
    scheduler.register(
        "check_deals_at_risk", job_check_deals_at_risk,
        _env_int("HEARTBEAT_DEAL_RISK_SEC", 21600),
    )
    scheduler.register(
        "snapshot_pipeline_metrics", job_snapshot_pipeline_metrics,
        _env_int("HEARTBEAT_METRICS_SNAPSHOT_SEC", 3600),
    )
    if heartbeat_enabled():
        scheduler.start()
    else:
        logger.info("Heartbeat disabled via HEARTBEAT_ENABLED=0")
    return scheduler
