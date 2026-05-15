# src/core/celery_app.py
from celery import Celery
from ..core.config import settings

celery_app = Celery(
    "auth_system",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["src.tasks.email_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_queues={
        "auth_tasks": {"exchange": "auth_tasks", "routing_key": "auth_tasks"},
    },
    task_default_queue="auth_tasks",
    task_default_routing_key="auth_tasks",
)
