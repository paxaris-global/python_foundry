from app.core.constants import RAG_SCORE_THRESHOLD


class FallbackStrategyResolver:
    def resolve(self, rag_context: list[dict], blueprint: dict) -> dict:
        if not rag_context:
            return {
                "strategy": "blueprint_only",
                "reason": "rag_empty",
                "blueprint_patterns": blueprint.get("architecture_patterns", []),
            }

        strong_hits = [item for item in rag_context if item.get("score") is not None and item["score"] >= RAG_SCORE_THRESHOLD]
        if strong_hits:
            return {
                "strategy": "rag_first",
                "reason": "strong_rag_matches",
                "strong_hits": len(strong_hits),
                "blueprint_patterns": blueprint.get("architecture_patterns", []),
            }

        return {
            "strategy": "hybrid_blueprint_rag",
            "reason": "rag_weak",
            "blueprint_patterns": blueprint.get("architecture_patterns", []),
        }
