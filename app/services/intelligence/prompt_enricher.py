from app.utils.json_utils import to_pretty_json


class PromptEnricher:
    def enrich(
        self,
        original_prompt: str,
        project_spec: dict,
        api_contract: dict,
        rag_context: list[dict],
        fallback_context: dict,
    ) -> str:
        rag_snippets = []
        for item in rag_context[:6]:
            rag_snippets.append(
                {
                    "score": item.get("score"),
                    "metadata": item.get("metadata", {}),
                    "content": item.get("content", "")[:500],
                }
            )

        frontend_spec = project_spec.get("frontend", {})
        ui_directives = {
            "ui_profile": frontend_spec.get("ui_profile", "professional"),
            "layout_style": frontend_spec.get("layout_style", "workspace"),
            "brand_tone": frontend_spec.get("brand_tone", "professional"),
            "visual_keywords": frontend_spec.get("visual_keywords", []),
            "theme_tokens": frontend_spec.get("theme_tokens", {}),
            "quality_bar": [
                "Use a modern, responsive layout with clear visual hierarchy",
                "Create reusable components and avoid plain boilerplate styling",
                "Prefer polished spacing, typography, and empty states",
                "Keep accessibility labels and keyboard-friendly interactions",
            ],
        }

        return (
            "You are generating production-grade full-stack code.\n"
            f"User Prompt: {original_prompt}\n\n"
            f"UIRequirements:\n{to_pretty_json(ui_directives)}\n\n"
            f"ProjectSpec:\n{to_pretty_json(project_spec)}\n\n"
            f"APIContract:\n{to_pretty_json(api_contract)}\n\n"
            f"RAGContext:\n{to_pretty_json(rag_snippets)}\n\n"
            f"FallbackContext:\n{to_pretty_json(fallback_context)}\n"
        )
