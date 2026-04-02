from typing import Optional

from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from app.core.config import get_settings
from app.core.logging import get_logger
from app.utils.url_utils import is_safe_url, normalize_url

logger = get_logger(__name__)


class SearchClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def search(self, query: str, max_results: Optional[int] = None) -> list[dict]:
        limit = max_results or self.settings.max_web_results
        results: list[dict] = []

        primary_provider = self.settings.search_provider.lower()
        fallback_provider = self.settings.fallback_search_provider.lower()

        try:
            results = self._search_via_provider(primary_provider, query, limit)
        except Exception as exc:
            logger.warning("Primary search provider %s failed: %s", primary_provider, exc)

        if not results and fallback_provider and fallback_provider != primary_provider:
            try:
                results = self._search_via_provider(fallback_provider, query, limit)
            except Exception as exc:
                logger.warning("Fallback search provider %s failed: %s", fallback_provider, exc)

        github_results = self._search_github_repositories(query, max(1, min(3, limit // 2)))
        return self._dedupe_results(results + github_results, limit)

    def _search_via_provider(self, provider: str, query: str, limit: int) -> list[dict]:
        if provider == "serpapi" and self.settings.search_api_key:
            return self._search_serpapi(query, limit)
        if provider == "duckduckgo":
            return self._search_duckduckgo(query, limit)
        if provider == "brave":
            return self._search_brave(query, limit)
        raise ValueError(f"Unsupported or misconfigured search provider: {provider}")

    def _search_serpapi(self, query: str, limit: int) -> list[dict]:
        engine = self.settings.search_engine or "google"
        params = {
            "q": query,
            "engine": engine,
            "api_key": self.settings.search_api_key,
            "num": min(limit, 10),
        }
        response = httpx.get(
            "https://serpapi.com/search.json",
            params=params,
            timeout=self.settings.search_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()

        organic_results = payload.get("organic_results", []) or payload.get("news_results", [])
        results = []
        for item in organic_results[:limit]:
            url = normalize_url(item.get("link", ""))
            if not is_safe_url(url):
                continue
            results.append(
                {
                    "title": item.get("title", ""),
                    "url": url,
                    "snippet": item.get("snippet", ""),
                    "provider": "serpapi",
                    "provider_engine": engine,
                    "source_type": "web",
                }
            )
        return results

    def _search_duckduckgo(self, query: str, limit: int) -> list[dict]:
        url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
        response = httpx.get(url, timeout=self.settings.search_timeout_seconds, follow_redirects=True)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        results = []
        for block in soup.select(".result"):
            link_tag = block.select_one("a.result__a")
            if not link_tag:
                continue
            href = normalize_url(link_tag.get("href", ""))
            if not is_safe_url(href):
                continue
            snippet_tag = block.select_one(".result__snippet")
            results.append(
                {
                    "title": link_tag.get_text(strip=True),
                    "url": href,
                    "snippet": snippet_tag.get_text(strip=True) if snippet_tag else "",
                    "provider": "duckduckgo",
                    "provider_engine": "html",
                    "source_type": "web",
                }
            )
            if len(results) >= limit:
                break

        return results

    def _search_brave(self, query: str, limit: int) -> list[dict]:
        headers = {"Accept": "application/json", "X-Subscription-Token": self.settings.search_api_key or ""}
        response = httpx.get(
            "https://api.search.brave.com/res/v1/web/search",
            params={"q": query, "count": min(limit, 10)},
            headers=headers,
            timeout=self.settings.search_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        results = []
        for item in payload.get("web", {}).get("results", [])[:limit]:
            url = normalize_url(item.get("url", ""))
            if not is_safe_url(url):
                continue
            results.append(
                {
                    "title": item.get("title", ""),
                    "url": url,
                    "snippet": item.get("description", ""),
                    "provider": "brave",
                    "provider_engine": "web",
                    "source_type": "web",
                }
            )
        return results

    def _search_github_repositories(self, query: str, limit: int) -> list[dict]:
        headers = {"Accept": "application/vnd.github+json"}
        if self.settings.github_token:
            headers["Authorization"] = f"Bearer {self.settings.github_token}"

        try:
            response = httpx.get(
                "https://api.github.com/search/repositories",
                params={"q": query, "per_page": limit, "sort": "stars", "order": "desc"},
                headers=headers,
                timeout=self.settings.search_timeout_seconds,
            )
            response.raise_for_status()
        except Exception as exc:
            logger.warning("GitHub repository search failed: %s", exc)
            return []

        payload = response.json()
        results = []
        for item in payload.get("items", [])[:limit]:
            url = normalize_url(item.get("html_url", ""))
            if not is_safe_url(url):
                continue
            results.append(
                {
                    "title": item.get("full_name", ""),
                    "url": url,
                    "snippet": item.get("description", "") or "",
                    "provider": "github",
                    "provider_engine": "rest_api",
                    "source_type": "repository",
                    "stars": item.get("stargazers_count", 0),
                }
            )
        return results

    @staticmethod
    def _dedupe_results(results: list[dict], limit: int) -> list[dict]:
        seen_urls: set[str] = set()
        deduped: list[dict] = []
        for item in results:
            url = item.get("url", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            deduped.append(item)
            if len(deduped) >= limit:
                break
        return deduped
