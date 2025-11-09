"""Routes for above-the-fold image optimization."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_auth_dependency
from app.models.image import ImageConversionRequest, ImageConversionResult, ImageJobStatusResponse
from app.models.job import JobStatus
from app.services import job_store
from app.tasks.image_tasks import process_image_conversion

router = APIRouter(prefix="/images", tags=["images"], dependencies=[Depends(get_auth_dependency)])


@router.post(
    "/convert",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue an image conversion job",
)
def enqueue_image_conversion(payload: ImageConversionRequest) -> dict:
    """Create a conversion job and dispatch to the worker."""

    job_id = f"img_{uuid.uuid4().hex}"
    serialized_payload = payload.model_dump(mode="json")
    job_store.create_job(
        job_id=job_id,
        job_type="image",
        payload=serialized_payload,
    )
    process_image_conversion.delay(job_id=job_id, payload=serialized_payload)
    return {"job_id": job_id, "status": JobStatus.queued}


@router.get(
    "/{job_id}",
    response_model=ImageJobStatusResponse,
    summary="Retrieve image conversion job status",
)
def get_image_job(job_id: str) -> ImageJobStatusResponse:
    """Return the current status of a job."""

    job = job_store.job_store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    result = None
    if job.result:
        result = ImageConversionResult.model_validate(job.result)

    detected_source = result.detected_image.source_url if result and result.detected_image else None
    payload_source = job.payload.get("source_url")

    return ImageJobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        source_url=payload_source or detected_source,
        asset_key=job.payload.get("asset_key"),
        created_at=job.created_at,
        updated_at=job.updated_at,
        result=result,
        error=job.error,
    )

