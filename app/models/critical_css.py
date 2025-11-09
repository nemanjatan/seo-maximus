"""Models for critical CSS extraction workflows."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import AnyHttpUrl, BaseModel, Field

from .job import JobStatus


class ViewportProfile(str):
    """Common viewport identifiers."""

    DESKTOP = "desktop"
    TABLET = "tablet"
    MOBILE = "mobile"


class CriticalCSSRequest(BaseModel):
    """Payload accepted by the critical CSS endpoint."""

    target_url: AnyHttpUrl
    template: str = Field(..., description="Template identifier for downstream consumers.")
    viewport_profiles: List[str] = Field(default_factory=lambda: ["desktop", "mobile"])
    auth_headers: Optional[Dict[str, str]] = Field(default=None, description="Optional request headers for auth.")


class DeferralInstructions(BaseModel):
    """Suggested snippet to defer remaining assets."""

    description: str
    snippet: str


class CriticalCSSResult(BaseModel):
    """Result payload for completed CSS extraction jobs."""

    critical_css: str
    defer_instructions: Optional[DeferralInstructions] = None
    viewports: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    artifacts: Dict[str, List[AnyHttpUrl]] = Field(default_factory=dict)


class CriticalCSSJobStatusResponse(BaseModel):
    """API response for CSS job status queries."""

    job_id: str
    status: JobStatus
    template: str
    target_url: AnyHttpUrl
    created_at: datetime
    updated_at: datetime
    result: Optional[CriticalCSSResult] = None
    error: Optional[str] = None

