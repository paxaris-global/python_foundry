import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.utils.url_utils import is_safe_url

logger = get_logger(__name__)


class PageFetcher:
    def __init__(self) -> None:
        self.settings = get_settings()

    def fetch(self, url: str) -> dict:
        if not is_safe_url(url):
            return {"url": url, "status": "skipped", "html": "", "error": "unsafe_url"}

        try:
            response = httpx.get(url, timeout=self.settings.search_timeout_seconds, follow_redirects=True)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            if "html" not in content_type and "text" not in content_type:
                return {"url": url, "status": "skipped", "html": "", "error": "unsupported_content_type"}
            return {"url": url, "status": "ok", "html": response.text, "error": None}
        except Exception as exc:
            logger.warning("Page fetch failed for %s: %s", url, exc)
            return {"url": url, "status": "error", "html": "", "error": str(exc)}
