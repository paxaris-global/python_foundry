class FeatureExtractor:
    TOKENS = [
        "authentication",
        "authorization",
        "dashboard",
        "reports",
        "booking",
        "catalog",
        "cart",
        "orders",
        "payments",
        "notifications",
        "analytics",
        "admin",
    ]

    def extract(self, page_data: dict) -> list[str]:
        text = (page_data.get("text") or "").lower()
        features = [token for token in self.TOKENS if token in text]
        return sorted(set(features))
