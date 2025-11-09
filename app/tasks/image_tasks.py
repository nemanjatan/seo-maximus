"""Celery tasks for image optimization."""

from __future__ import annotations

from app.core.logging import get_logger
from app.models.image import ImageConversionRequest
from app.services import job_store
from app.services.image_optimizer import image_optimizer
from app.worker.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(name="image.process_conversion")
def process_image_conversion(job_id: str, payload: dict) -> dict:
    """Execute the image conversion flow."""

    logger.info("image_conversion_task_started", job_id=job_id)
    try:
        job_store.mark_processing(job_id)
        request = ImageConversionRequest(**payload)
        result = image_optimizer.convert(request)
        result_payload = result.model_dump(mode="json")
        job_store.mark_completed(job_id, result_payload)
        logger.info("image_conversion_task_completed", job_id=job_id)
        return result_payload
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("image_conversion_task_failed", job_id=job_id, error=str(exc))
        job_store.mark_failed(job_id, str(exc))
        raise

