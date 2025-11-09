"""Pydantic models for image optimization workflows."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import AnyHttpUrl, BaseModel, Field, field_validator, model_validator

from .job import JobStatus


class ImageFormat(str):
    """Supported output image formats."""

    WEBP = "webp"
    AVIF = "avif"


class HeroImagePosition(BaseModel):
    """Bounding box details for detected hero image."""

    top: float
    left: float
    width: float
    height: float
    visible_area: float


class HeroImageDetection(BaseModel):
    """Metadata about an automatically detected hero image."""

    source_url: AnyHttpUrl
    selector: str
    score: float
    position: HeroImagePosition
    natural_width: Optional[int] = None
    natural_height: Optional[int] = None
    loading: Optional[str] = None


class ImageConversionRequest(BaseModel):
    """Payload accepted by the image optimization endpoint."""

    source_url: Optional[AnyHttpUrl] = Field(
        default=None,
        description="Direct URL to the asset to optimize.",
    )
    target_page_url: Optional[AnyHttpUrl] = Field(
        default=None,
        description="Page URL used to auto-detect the above-the-fold image.",
    )
    asset_key: Optional[str] = Field(default=None, description="Identifier used by consuming system.")
    prefetch: bool = Field(default=True, description="Whether to generate a <link rel='prefetch'> tag.")
    formats: List[str] = Field(default_factory=lambda: ["webp"], description="Desired output formats.")

    @model_validator(mode="after")
    def ensure_source_or_page(self) -> "ImageConversionRequest":
        """Validate that at least one source reference is provided."""

        if not self.source_url and not self.target_page_url:
            raise ValueError("Either 'source_url' or 'target_page_url' must be provided.")
        return self

    @field_validator("formats", mode="before")
    @classmethod
    def normalize_formats(cls, value: List[str]) -> List[str]:
        """Ensure formats list is not empty."""

        if not value:
            return ["webp"]
        return value


class OptimizedImage(BaseModel):
    """Metadata for an optimized image variant."""

    format: str
    url: str
    bytes: int
    savings_percent: float


class ImageConversionResult(BaseModel):
    """Result payload for completed image conversion jobs."""

    optimized_assets: List[OptimizedImage]
    prefetch_tag: Optional[str] = None
    img_snippet: Optional[str] = None
    detected_image: Optional[HeroImageDetection] = None


class ImageJobStatusResponse(BaseModel):
    """API response for image job status queries."""

    job_id: str
    status: JobStatus
    source_url: Optional[AnyHttpUrl] = None
    asset_key: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    result: Optional[ImageConversionResult] = None
    error: Optional[str] = None

