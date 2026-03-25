import re


class PromptParser:
    def parse_prompt(self, prompt: str) -> dict:
        lowered = prompt.lower()
        tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]+", lowered)

        feature_hints = []
        for keyword in ["auth", "dashboard", "crud", "reports", "payments", "analytics"]:
            if keyword in lowered:
                feature_hints.append(keyword)

        entities = []
        for candidate in ["customer", "user", "order", "invoice", "product", "report"]:
            if candidate in lowered:
                entities.append(candidate)

        return {
            "summary": prompt.strip(),
            "tokens": tokens[:120],
            "feature_hints": sorted(set(feature_hints)),
            "entities": sorted(set(entities)),
        }
