"""Service wrapper for critical CSS extraction."""

from __future__ import annotations

import textwrap
from typing import Dict, List

from app.core.config import settings
from app.models.critical_css import (
    CriticalCSSRequest,
    CriticalCSSResult,
    DeferralInstructions,
)


class CriticalCSSExtractor:
    """Stubbed extractor that mimics Playwright-driven CSS coverage."""

    def extract(self, request: CriticalCSSRequest) -> CriticalCSSResult:
        """Return synthesized critical CSS for MVP scaffolding."""

        viewports = self._resolve_viewports(request.viewport_profiles)

        critical_css = textwrap.dedent(
            """
            /* Critical CSS placeholder */
            body { margin: 0; font-family: system-ui, sans-serif; }
            header.hero { min-height: 60vh; display: grid; place-items: center; }
            header.hero h1 { font-size: clamp(2.5rem, 5vw, 4rem); }
            """
        ).strip()

        defer = DeferralInstructions(
            description="Swap main stylesheet once loaded to avoid render-blocking.",
            snippet=(
                "<link rel=\"preload\" href=\"/static/app.css\" as=\"style\" "
                "onload=\"this.rel='stylesheet'\">"
            ),
        )

        artifacts: Dict[str, List[str]] = {}

        return CriticalCSSResult(
            critical_css=critical_css,
            defer_instructions=defer,
            viewports=viewports,
            artifacts=artifacts,
        )

    def _resolve_viewports(self, profiles: List[str]) -> Dict[str, Dict[str, int]]:
        """Translate profile identifiers into width/height pairs."""

        mapping = {
            "desktop": {"width": 1440, "height": 900},
            "tablet": {"width": 1024, "height": 768},
            "mobile": {"width": 390, "height": 844},
        }
        fallback = settings.playwright_viewports

        resolved: Dict[str, Dict[str, int]] = {}
        for profile in profiles or fallback:
            key = profile.lower()
            if key in mapping:
                resolved[key] = mapping[key]

        if not resolved:
            resolved["desktop"] = mapping["desktop"]

        return resolved


critical_css_extractor = CriticalCSSExtractor()

