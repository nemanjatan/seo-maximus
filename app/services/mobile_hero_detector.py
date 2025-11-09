"""Detects above-the-fold hero images for mobile viewports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.parse import urljoin

from playwright.sync_api import Playwright, TimeoutError as PlaywrightTimeoutError, sync_playwright

from app.core.logging import get_logger
from app.models.image import HeroImageDetection, HeroImagePosition

logger = get_logger(__name__)

MOBILE_VIEWPORT = {"width": 390, "height": 844, "device_scale_factor": 3}
MOBILE_USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
)


@dataclass
class _DetectionCandidate:
    src: str
    selector: str
    score: float
    position: Dict[str, float]
    natural_width: Optional[int]
    natural_height: Optional[int]
    loading: Optional[str]


class MobileHeroDetector:
    """Encapsulates Playwright logic for detecting mobile hero images."""

    def __init__(self, viewport: Optional[Dict[str, int]] = None) -> None:
        self.viewport = viewport or MOBILE_VIEWPORT

    def detect(self, page_url: str) -> Optional[HeroImageDetection]:
        """Return the best hero candidate for the supplied page URL."""

        try:
            with sync_playwright() as p:
                return self._detect_with_playwright(p, page_url)
        except PlaywrightTimeoutError as exc:
            logger.warning("hero_detection_timeout", url=page_url, error=str(exc))
            return None
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception("hero_detection_failed", url=page_url, error=str(exc))
            return None

    def _detect_with_playwright(self, playwright: Playwright, page_url: str) -> Optional[HeroImageDetection]:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={k: v for k, v in self.viewport.items() if k in {"width", "height"}},
            device_scale_factor=self.viewport.get("device_scale_factor", 2),
            user_agent=MOBILE_USER_AGENT,
            is_mobile=True,
            has_touch=True,
        )

        try:
            page = context.new_page()
            page.goto(page_url, wait_until="networkidle", timeout=30_000)
            page.wait_for_timeout(1500)

            candidates = self._collect_candidates(page)
            if not candidates:
                page.evaluate("window.scrollBy(0, window.innerHeight * 0.25);")
                page.wait_for_timeout(500)
                candidates = self._collect_candidates(page)

            if not candidates:
                return None

            best = max(candidates, key=lambda c: c.score)
            absolute_url = urljoin(page_url, best.src)

            position = HeroImagePosition(
                top=best.position["top"],
                left=best.position["left"],
                width=best.position["width"],
                height=best.position["height"],
                visible_area=best.position["visibleArea"],
            )

            return HeroImageDetection(
                source_url=absolute_url,
                selector=best.selector,
                score=best.score,
                position=position,
                natural_width=best.natural_width,
                natural_height=best.natural_height,
                loading=best.loading,
            )
        finally:
            context.close()
            browser.close()

    def _collect_candidates(self, page: Any) -> list[_DetectionCandidate]:
        raw_candidates = page.evaluate(
            """
            () => {
              const viewportWidth = window.innerWidth;
              const viewportHeight = window.innerHeight;

              const cssPath = (el) => {
                if (el.id) {
                  return `#${el.id}`;
                }
                const parts = [];
                while (el && el.nodeType === Node.ELEMENT_NODE) {
                  let selector = el.nodeName.toLowerCase();
                  if (el.className) {
                    const className = el.className.trim().split(/\\s+/).filter(Boolean).join('.');
                    if (className) selector += `.${className}`;
                  }
                  const siblings = Array.from(el.parentNode ? el.parentNode.children : []).filter(
                    sib => sib.nodeName === el.nodeName
                  );
                  if (siblings.length > 1) {
                    const index = siblings.indexOf(el) + 1;
                    selector += `:nth-of-type(${index})`;
                  }
                  parts.unshift(selector);
                  el = el.parentNode;
                }
                return parts.join(" > ");
              };

              const computeVisibleArea = (rect) => {
                const visibleWidth = Math.max(0, Math.min(rect.right, viewportWidth) - Math.max(rect.left, 0));
                const visibleHeight = Math.max(0, Math.min(rect.bottom, viewportHeight) - Math.max(rect.top, 0));
                return visibleWidth * visibleHeight;
              };

              const isMeaningful = (rect) => rect.width * rect.height > 5000;

              const elements = Array.from(document.querySelectorAll("img, picture"));
              const results = [];

              for (const element of elements) {
                let target = element;
                if (element.nodeName.toLowerCase() === "picture") {
                  const imgChild = element.querySelector("img");
                  if (!imgChild) continue;
                  target = imgChild;
                }

                const rect = target.getBoundingClientRect();
                const visibleArea = computeVisibleArea(rect);
                if (!visibleArea) continue;
                if (!isMeaningful(rect)) continue;

                const src =
                  target.currentSrc ||
                  target.getAttribute("srcset")?.split(",")[0]?.trim().split(" ")[0] ||
                  target.getAttribute("data-src") ||
                  target.getAttribute("data-lazy-src") ||
                  target.getAttribute("src") ||
                  "";
                if (!src) continue;

                const loading = target.getAttribute("loading") || "";
                const naturalWidth = target.naturalWidth || 0;
                const naturalHeight = target.naturalHeight || 0;

                const topPenalty = Math.max(rect.top, 0);
                const score = visibleArea - topPenalty * 25;

                results.push({
                  src,
                  selector: cssPath(element),
                  score,
                  position: {
                    top: rect.top,
                    left: rect.left,
                    width: rect.width,
                    height: rect.height,
                    visibleArea,
                  },
                  naturalWidth,
                  naturalHeight,
                  loading,
                });
              }

              return results;
            }
            """
        )

        candidates: list[_DetectionCandidate] = []
        for entry in raw_candidates or []:
            try:
                candidates.append(
                    _DetectionCandidate(
                        src=str(entry["src"]),
                        selector=str(entry["selector"]),
                        score=float(entry["score"]),
                        position={
                            "top": float(entry["position"]["top"]),
                            "left": float(entry["position"]["left"]),
                            "width": float(entry["position"]["width"]),
                            "height": float(entry["position"]["height"]),
                            "visibleArea": float(entry["position"]["visibleArea"]),
                        },
                        natural_width=int(entry.get("naturalWidth") or 0),
                        natural_height=int(entry.get("naturalHeight") or 0),
                        loading=str(entry.get("loading") or ""),
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue

        return candidates


mobile_hero_detector = MobileHeroDetector()

