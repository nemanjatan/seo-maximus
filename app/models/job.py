"""Shared job models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Possible states for asynchronous jobs."""

    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class JobMetadata(BaseModel):
    """Metadata associated with a job."""

    job_id: str
    job_type: str
    status: JobStatus
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    error: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None

    def with_status(self, status: JobStatus) -> "JobMetadata":
        """Return a copy with an updated status."""

        return self.model_copy(update={"status": status, "updated_at": datetime.utcnow()})

    def with_result(self, result: Dict[str, Any]) -> "JobMetadata":
        """Return a copy with an updated result."""

        return self.model_copy(update={"result": result, "status": JobStatus.completed, "updated_at": datetime.utcnow()})

    def with_error(self, message: str) -> "JobMetadata":
        """Return a copy with an error message and failed status."""

        return self.model_copy(
            update={
                "error": message,
                "status": JobStatus.failed,
                "updated_at": datetime.utcnow(),
            }
        )

