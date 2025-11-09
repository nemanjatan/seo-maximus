"""Celery application configuration."""

from celery import Celery

from app.core.config import settings

celery_app = Celery("seo_maximus")

broker_url = settings.celery_broker_url or settings.redis_url
result_backend = settings.celery_result_backend or settings.redis_url

celery_app.conf.update(
    broker_url=broker_url,
    result_backend=result_backend,
    task_default_queue="seo_maximus",
    task_soft_time_limit=120,
    task_time_limit=180,
    worker_max_tasks_per_child=100,
    task_track_started=True,
    task_always_eager=settings.debug,
)

celery_app.autodiscover_tasks(["app.tasks"])

