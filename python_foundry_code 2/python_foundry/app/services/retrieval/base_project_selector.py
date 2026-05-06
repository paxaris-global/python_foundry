from app.models.project import Project
from app.services.retrieval.project_similarity import ProjectSimilarity


class BaseProjectSelector:
    def __init__(self):
        self.similarity = ProjectSimilarity()

    def score_candidates(self, prompt: str, features: list[str], candidates: list[Project]) -> list[dict]:
        scored = []
        for project in candidates:
            score = self.similarity.score(prompt, features, project)
            scored.append({"project": project, "score": score})

        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored

    def determine_mode(
        self,
        scored_candidates: list[dict],
        mode_preference: str = "auto",
        reuse_threshold: float = 0.88,
        adapt_threshold: float = 0.62,
        scaffold_threshold: float = 0.35,
    ) -> dict:
        if not scored_candidates:
            return {"mode": "generate", "selected": None, "score": 0.0, "candidates": []}

        best = scored_candidates[0]
        preference = (mode_preference or "auto").lower()
        if preference in {"reuse", "adapt", "generate", "hybrid_scaffold"} and preference != "auto":
            mode = preference if preference == "generate" or best["project"] is not None else "generate"
        elif best["score"] >= reuse_threshold:
            mode = "reuse"
        elif best["score"] >= adapt_threshold:
            mode = "adapt"
        elif best["score"] >= scaffold_threshold:
            mode = "hybrid_scaffold"
        else:
            mode = "generate"

        return {
            "mode": mode,
            "selected": best["project"] if mode != "generate" else None,
            "score": best["score"],
            "candidates": [
                {"project_id": str(item["project"].id), "name": item["project"].name, "score": item["score"]}
                for item in scored_candidates[:5]
            ],
        }

    def select(
        self,
        prompt: str,
        features: list[str],
        candidates: list[Project],
        mode_preference: str = "auto",
        reuse_threshold: float = 0.88,
        adapt_threshold: float = 0.62,
    ) -> dict:
        scored = self.score_candidates(prompt, features, candidates)
        return self.determine_mode(
            scored_candidates=scored,
            mode_preference=mode_preference,
            reuse_threshold=reuse_threshold,
            adapt_threshold=adapt_threshold,
        )
