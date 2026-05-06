import multiprocessing
multiprocessing.set_start_method("spawn", force=True)
from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "ai_codegen",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.generation_tasks"],
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
    task_time_limit=1800,
    task_soft_time_limit=1700,
)

celery_app.autodiscover_tasks(["app"])
