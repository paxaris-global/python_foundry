class WebKnowledgeBuilder:
    def build(self, results: list[dict], extracted_items: list[dict]) -> dict:
        all_features: set[str] = set()
        all_entities: set[str] = set()
        all_routes: set[str] = set()
        all_components: set[str] = set()
        all_backend_patterns: set[str] = set()
        suggested_arch: set[str] = set()

        docs_for_rag: list[dict] = []

        for item in extracted_items:
            all_features.update(item.get("features", []))
            all_entities.update(item.get("entities", []))
            all_routes.update(item.get("routes", []))
            all_components.update(item.get("components", []))
            all_backend_patterns.update(item.get("backend_patterns", []))
            suggested_arch.update(item.get("ui_patterns", []))

            text_blob = item.get("text", "")
            if text_blob:
                docs_for_rag.append(
                    {
                        "url": item.get("url"),
                        "content": text_blob[:8000],
                        "language": "text",
                        "trust_score": item.get("trust_score", 0.0),
                    }
                )

        return {
            "trusted_results": results,
            "features": sorted(all_features),
            "entities": sorted(all_entities),
            "routes": sorted(all_routes),
            "components": sorted(all_components),
            "backend_patterns": sorted(all_backend_patterns),
            "suggested_architecture": sorted(suggested_arch),
            "docs_for_rag": docs_for_rag,
        }
