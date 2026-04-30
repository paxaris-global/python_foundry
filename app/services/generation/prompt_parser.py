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

        ui_profile = "professional"
        if any(word in lowered for word in ["minimal", "clean", "simple"]):
            ui_profile = "minimal"
        elif any(word in lowered for word in ["luxury", "premium", "elegant"]):
            ui_profile = "luxury"
        elif any(word in lowered for word in ["vibrant", "playful", "creative"]):
            ui_profile = "vibrant"

        layout_style = "workspace"
        if any(word in lowered for word in ["dashboard", "admin", "analytics", "management"]):
            layout_style = "dashboard"
        elif any(word in lowered for word in ["landing", "marketing", "homepage"]):
            layout_style = "landing"

        brand_tone = "professional"
        if any(word in lowered for word in ["enterprise", "corporate", "b2b"]):
            brand_tone = "enterprise"
        elif any(word in lowered for word in ["friendly", "consumer", "b2c"]):
            brand_tone = "consumer"

        visual_keywords = []
        for word in ["modern", "professional", "premium", "minimal", "dark", "light", "dashboard"]:
            if word in lowered:
                visual_keywords.append(word)

        return {
            "summary": prompt.strip(),
            "tokens": tokens[:120],
            "feature_hints": sorted(set(feature_hints)),
            "entities": sorted(set(entities)),
            "ui_profile": ui_profile,
            "layout_style": layout_style,
            "brand_tone": brand_tone,
            "visual_keywords": sorted(set(visual_keywords)),
        }
