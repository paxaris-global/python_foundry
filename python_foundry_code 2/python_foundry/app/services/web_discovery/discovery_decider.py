class DiscoveryDecider:
    DOMAIN_BENEFIT_KEYWORDS = {
        "crm",
        "hotel",
        "erp",
        "pos",
        "ecommerce",
        "booking",
        "dashboard",
        "saas",
        "inventory",
        "hospital",
    }

    ADVANCED_UI_KEYWORDS = {
        "modern ui",
        "production",
        "saas-like",
        "responsive",
        "admin panel",
        "analytics",
        "enterprise",
    }

    def decide(
        self,
        prompt: str,
        domain: str,
        website_like: str | None,
        strong_reusable_project: bool,
        rag_confidence: float,
        adaptation_score: float,
    ) -> dict:
        lowered_prompt = prompt.lower()
        reasons: list[str] = []

        if website_like:
            reasons.append("website_like_provided")

        if self._is_underspecified(lowered_prompt, domain):
            reasons.append("domain_heavy_but_underspecified")

        if not strong_reusable_project:
            reasons.append("no_strong_reusable_project")

        if rag_confidence < 0.45:
            reasons.append("low_rag_confidence")

        if 0.0 < adaptation_score < 0.62:
            reasons.append("weak_adaptation_candidate")

        if any(keyword in lowered_prompt for keyword in self.ADVANCED_UI_KEYWORDS):
            reasons.append("advanced_ui_or_production_requested")

        if domain in self.DOMAIN_BENEFIT_KEYWORDS or any(keyword in lowered_prompt for keyword in self.DOMAIN_BENEFIT_KEYWORDS):
            reasons.append("domain_benefits_from_reference_discovery")

        return {
            "should_run": bool(reasons),
            "reasons": reasons,
            "rag_confidence": rag_confidence,
            "adaptation_score": adaptation_score,
            "strong_reusable_project": strong_reusable_project,
        }

    @staticmethod
    def _is_underspecified(prompt: str, domain: str) -> bool:
        if len(prompt.split()) > 18:
            return False
        domain_terms = [domain.replace("_", " "), "dashboard", "management", "system", "portal"]
        return any(term in prompt for term in domain_terms)
