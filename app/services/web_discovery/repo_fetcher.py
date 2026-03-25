from urllib.parse import urlparse

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RepoFetcher:
    def __init__(self) -> None:
        self.settings = get_settings()

    def fetch_github_repo(self, url: str) -> dict:
        try:
            owner, repo = self._extract_owner_repo(url)
        except ValueError:
            return {"url": url, "status": "skipped", "readme": "", "metadata": {}}

        metadata = {}
        readme = ""
        headers = {"Accept": "application/vnd.github+json"}
        if self.settings.github_token:
            headers["Authorization"] = f"Bearer {self.settings.github_token}"

        try:
            meta_resp = httpx.get(
                f"https://api.github.com/repos/{owner}/{repo}",
                headers=headers,
                timeout=self.settings.search_timeout_seconds,
            )
            if meta_resp.status_code == 200:
                metadata = meta_resp.json()

            readme_resp = httpx.get(
                f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/README.md",
                timeout=self.settings.search_timeout_seconds,
                follow_redirects=True,
            )
            if readme_resp.status_code == 200:
                readme = readme_resp.text

            return {
                "url": url,
                "status": "ok",
                "readme": readme,
                "metadata": metadata,
                "owner": owner,
                "repo": repo,
            }
        except Exception as exc:
            logger.warning("GitHub repo fetch failed for %s: %s", url, exc)
            return {"url": url, "status": "error", "readme": "", "metadata": {}, "error": str(exc)}

    @staticmethod
    def _extract_owner_repo(url: str) -> tuple[str, str]:
        parsed = urlparse(url)
        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) < 2:
            raise ValueError("Invalid GitHub repository URL")
        return parts[0], parts[1]
