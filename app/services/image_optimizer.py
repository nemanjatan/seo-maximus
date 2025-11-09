"""Service wrapper for TinyPNG image optimization."""

from __future__ import annotations

from typing import Dict, List, Optional

import httpx
import tinify
from tinify import Error as TinifyError

from app.core.config import settings
from app.core.logging import get_logger
from app.models.image import (
    HeroImageDetection,
    ImageConversionRequest,
    ImageConversionResult,
    OptimizedImage,
)
from app.services.mobile_hero_detector import mobile_hero_detector

logger = get_logger(__name__)


class ThirdPartyImageOptimizer:
    """Integrates with TinyPNG (Tinify) to optimize and convert images."""

    def __init__(self, client: httpx.Client | None = None) -> None:
        self._client = client or httpx.Client(timeout=60.0)
        self._tinify_configured = False

    def convert(self, request: ImageConversionRequest) -> ImageConversionResult:
        """Convert the provided image using TinyPNG/TinyJPG."""

        source_url, detection = self._resolve_source(request)
        optimized_variants = self._perform_conversion(source_url, request.formats)

        prefetch_tag = None
        if request.prefetch and optimized_variants:
            first_url = optimized_variants[0].url
            if not str(first_url).startswith("data:"):
                prefetch_tag = f'<link rel="prefetch" href="{first_url}" as="image">'

        img_snippet = None
        if optimized_variants:
            variant = optimized_variants[0]
            img_snippet = (
                f'<img src="{variant.url}" type="image/{variant.format}" alt="" loading="eager" />'
            )

        return ImageConversionResult(
            optimized_assets=optimized_variants,
            prefetch_tag=prefetch_tag,
            img_snippet=img_snippet,
            detected_image=detection,
        )

    def _resolve_source(self, request: ImageConversionRequest) -> tuple[str, Optional[HeroImageDetection]]:
        """Determine the URL to optimize, optionally auto-detecting via Playwright."""

        if request.source_url:
            return str(request.source_url), None

        if not request.target_page_url:
            raise RuntimeError("Neither source_url nor target_page_url provided for conversion.")

        detection = mobile_hero_detector.detect(str(request.target_page_url))
        if not detection:
            raise RuntimeError("Unable to detect an above-the-fold image for the supplied page.")

        return str(detection.source_url), detection

    def _perform_conversion(self, source_url: str, formats: List[str]) -> List[OptimizedImage]:
        """Perform the TinyPNG conversion flow for the requested formats."""

        self._ensure_tinify_configured()
        source_bytes = self._fetch_source(source_url)
        normalized_formats = self._normalize_formats(formats)

        variants: List[OptimizedImage] = []
        for fmt in normalized_formats:
            try:
                variant = self._process_variant(fmt, source_bytes)
            except TinifyError as exc:
                logger.error("tinify_conversion_failed", format=fmt, error=str(exc))
                raise RuntimeError(f"TinyPNG conversion failed ({fmt}): {exc}") from exc

            variants.append(variant)

        return variants

    def _process_variant(self, fmt: str, source_bytes: bytes) -> OptimizedImage:
        """Compress and convert the image to a single format."""

        convert_types = self._format_to_mime(fmt)
        source = tinify.from_buffer(source_bytes)
        if convert_types:
            result_obj = source.convert(type=convert_types)
        else:
            result_obj = source

        buffer = result_obj.to_buffer()
        optimized_size = len(buffer)

        original_size = len(source_bytes)
        savings_percent = 0.0
        if original_size:
            savings_percent = round(max(0.0, (1 - (optimized_size / original_size)) * 100), 1)

        import base64

        mime = convert_types[0] if convert_types else f"image/{fmt}"
        data_url = f"data:{mime};base64,{base64.b64encode(buffer).decode('ascii')}"

        return OptimizedImage(
            format=fmt,
            url=data_url,
            bytes=int(optimized_size),
            savings_percent=savings_percent,
        )

    def _fetch_source(self, url: str) -> bytes:
        """Download the source image into memory."""

        response = self._client.get(str(url))
        response.raise_for_status()
        return response.content

    def _ensure_tinify_configured(self) -> None:
        """Configure tinify API key if provided."""

        if not settings.tinypng_api_key:
            raise RuntimeError("TinyPNG API key is not configured in settings.")

        if not self._tinify_configured or tinify.key != settings.tinypng_api_key:
            tinify.key = settings.tinypng_api_key
            self._tinify_configured = True

    @staticmethod
    def _normalize_formats(formats: List[str]) -> List[str]:
        """Ensure formats are unique and lowercase."""

        seen: Dict[str, None] = {}
        for fmt in formats or ["webp"]:
            fmt_lower = fmt.lower()
            if fmt_lower not in seen:
                seen[fmt_lower] = None
        return list(seen.keys())

    @staticmethod
    def _format_to_mime(fmt: str) -> List[str]:
        """Return TinyPNG MIME type list for the requested format."""

        mapping = {
            "webp": ["image/webp"],
            "avif": ["image/avif"],
            "jpeg": ["image/jpeg"],
            "jpg": ["image/jpeg"],
            "png": ["image/png"],
        }
        return mapping.get(fmt, [])


image_optimizer = ThirdPartyImageOptimizer()