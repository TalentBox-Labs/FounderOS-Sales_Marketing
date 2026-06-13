from __future__ import annotations

from celery import Celery

from revenue_os.config import settings

celery_app = Celery(
    "revenue_os",
    broker=settings.REDIS_URL or "redis://localhost:6379/0",
    backend=settings.REDIS_URL or "redis://localhost:6379/0",
    include=[
        "revenue_os.tasks.leads",
        "revenue_os.tasks.outreach",
        "revenue_os.tasks.agents",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "process-outreach-sequences": {
            "task": "revenue_os.tasks.outreach.process_outreach_sequences",
            "schedule": 1800.0,
        },
        "sync-gmail-inbox": {
            "task": "revenue_os.tasks.email_sync.sync_gmail_inbox",
            "schedule": 300.0,
        },
    },
)
