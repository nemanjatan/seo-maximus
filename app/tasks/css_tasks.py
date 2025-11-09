"""Celery tasks for critical CSS extraction."""

from __future__ import annotations

from app.core.logging import get_logger
from app.models.critical_css import CriticalCSSRequest
from app.services import job_store
from app.services.critical_css import critical_css_extractor
from app.worker.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(name="critical_css.generate")
def generate_critical_css(job_id: str, payload: dict) -> dict:
    """Produce critical CSS using the extractor service."""

    logger.info("critical_css_task_started", job_id=job_id)
    try:
        job_store.mark_processing(job_id)
        request = CriticalCSSRequest(**payload)
        result = critical_css_extractor.extract(request)
        result_payload = result.model_dump(mode="json")
        job_store.mark_completed(job_id, result_payload)
        logger.info("critical_css_task_completed", job_id=job_id)
        return result_payload
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("critical_css_task_failed", job_id=job_id, error=str(exc))
        job_store.mark_failed(job_id, str(exc))
        raise

