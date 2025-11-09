"""Routes for critical CSS extraction."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_auth_dependency
from app.models.critical_css import (
    CriticalCSSJobStatusResponse,
    CriticalCSSRequest,
    CriticalCSSResult,
)
from app.models.job import JobStatus
from app.services import job_store
from app.tasks.css_tasks import generate_critical_css

router = APIRouter(prefix="/critical-css", tags=["critical-css"], dependencies=[Depends(get_auth_dependency)])


@router.post(
    "/generate",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue a critical CSS generation job",
)
def enqueue_critical_css(payload: CriticalCSSRequest) -> dict:
    """Create a job to generate critical CSS for the provided target URL."""

    job_id = f"css_{uuid.uuid4().hex}"
    job_store.create_job(
        job_id=job_id,
        job_type="critical_css",
        payload=payload.model_dump(),
    )
    generate_critical_css.delay(job_id=job_id, payload=payload.model_dump())
    return {"job_id": job_id, "status": JobStatus.queued}


@router.get(
    "/{job_id}",
    response_model=CriticalCSSJobStatusResponse,
    summary="Retrieve critical CSS job status",
)
def get_critical_css_job(job_id: str) -> CriticalCSSJobStatusResponse:
    """Return job status and resulting CSS if available."""

    job = job_store.job_store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    result = None
    if job.result:
        result = CriticalCSSResult.model_validate(job.result)

    return CriticalCSSJobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        template=job.payload.get("template"),
        target_url=job.payload.get("target_url"),
        created_at=job.created_at,
        updated_at=job.updated_at,
        result=result,
        error=job.error,
    )

