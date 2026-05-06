from app.core.config import get_settings
from app.utils.url_utils import domain_of


class TrustedSourceFilter:
    LOW_QUALITY_TOKENS = {"pinterest", "facebook", "instagram", "youtube", "tiktok"}

    def __init__(self) -> None:
        self.settings = get_settings()

    def filter(self, results: list[dict]) -> list[dict]:
        allowed = self.settings.allowed_domains_set
        denied = self.settings.denied_domains_set

        filtered = []
        for item in results:
            url = item.get("url", "")
            domain = domain_of(url)
            if not domain:
                continue
            if any(domain == denied_domain or domain.endswith(f".{denied_domain}") for denied_domain in denied):
                continue
            if any(token in domain for token in self.LOW_QUALITY_TOKENS):
                continue

            trust_score = 0.25
            if any(domain == allowed_domain or domain.endswith(f".{allowed_domain}") for allowed_domain in allowed):
                trust_score = 0.92
            elif domain == "github.com" or domain.endswith(".github.com"):
                trust_score = 0.96
            elif domain.startswith("docs.") or ".docs." in domain or domain.endswith(".dev"):
                trust_score = 0.85
            elif item.get("source_type") == "repository":
                trust_score = 0.88

            snippet = (item.get("snippet") or "").lower()
            if "official" in snippet:
                trust_score += 0.03
            if "demo" in snippet or "reference" in snippet:
                trust_score += 0.02

            filtered.append(
                {
                    **item,
                    "domain": domain,
                    "trust_score": round(min(trust_score, 0.99), 3),
                }
            )

        return filtered
