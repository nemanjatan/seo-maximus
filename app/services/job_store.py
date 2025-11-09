"""In-memory job store used for the MVP scaffolding."""

from __future__ import annotations

from collections.abc import Mapping
from threading import Lock
from typing import Dict, Optional

from app.models.job import JobMetadata, JobStatus


class InMemoryJobStore:
    """Simple thread-safe job registry. Replace with persistent storage in production."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._jobs: Dict[str, JobMetadata] = {}

    def create_job(self, job: JobMetadata) -> None:
        with self._lock:
            self._jobs[job.job_id] = job

    def update_job(self, job_id: str, job: JobMetadata) -> None:
        with self._lock:
            if job_id not in self._jobs:
                raise KeyError(f"Job {job_id} not found")
            self._jobs[job_id] = job

    def get_job(self, job_id: str) -> Optional[JobMetadata]:
        with self._lock:
            return self._jobs.get(job_id)

    def all_jobs(self) -> Mapping[str, JobMetadata]:
        with self._lock:
            return dict(self._jobs)


job_store = InMemoryJobStore()


def create_job(job_id: str, job_type: str, payload: dict) -> JobMetadata:
    """Register a new job in queued state."""

    job = JobMetadata(job_id=job_id, job_type=job_type, status=JobStatus.queued, payload=payload)
    job_store.create_job(job)
    return job


def mark_processing(job_id: str) -> JobMetadata:
    """Mark job as in-flight."""

    job = job_store.get_job(job_id)
    if not job:
        raise KeyError(f"Job {job_id} not found")
    updated = job.with_status(JobStatus.processing)
    job_store.update_job(job_id, updated)
    return updated


def mark_completed(job_id: str, result: dict) -> JobMetadata:
    """Mark job as completed with result."""

    job = job_store.get_job(job_id)
    if not job:
        raise KeyError(f"Job {job_id} not found")
    updated = job.with_result(result)
    job_store.update_job(job_id, updated)
    return updated


def mark_failed(job_id: str, message: str) -> JobMetadata:
    """Mark job as failed."""

    job = job_store.get_job(job_id)
    if not job:
        raise KeyError(f"Job {job_id} not found")
    updated = job.with_error(message)
    job_store.update_job(job_id, updated)
    return updated

