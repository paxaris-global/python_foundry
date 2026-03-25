class ResultRanker:
    def rank(self, query: str, results: list[dict]) -> list[dict]:
        words = {word.lower() for word in query.split() if len(word) > 2}

        def score(item: dict) -> float:
            text = f"{item.get('title', '')} {item.get('snippet', '')}".lower()
            overlap = sum(1 for word in words if word in text)
            trust = float(item.get("trust_score", 0.0)) * 4.0
            provider_bonus = 0.0
            if item.get("source_type") == "repository":
                provider_bonus += 0.4
            if item.get("provider") == "serpapi":
                provider_bonus += 0.25
            if item.get("domain", "").startswith("docs."):
                provider_bonus += 0.2
            return trust + float(overlap) + provider_bonus

        ordered = sorted(results, key=score, reverse=True)
        for index, item in enumerate(ordered, start=1):
            item["rank"] = index
            item["rank_score"] = round(score(item), 4)
        return ordered
