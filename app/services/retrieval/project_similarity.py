import re

from app.models.project import Project


class ProjectSimilarity:
    @staticmethod
    def _tokenize(value: str) -> set[str]:
        return {token for token in re.findall(r"\w+", value.lower()) if len(token) > 2}

    def score(self, prompt: str, features: list[str], project: Project) -> float:
        prompt_tokens = self._tokenize(prompt)
        prompt_tokens.update(self._tokenize(" ".join(features)))

        project_text = " ".join(
            [
                project.name or "",
                project.description or "",
                " ".join((project.manifest or {}).get("features", [])),
                " ".join((project.validation_report or {}).get("missing", [])),
            ]
        )
        project_tokens = self._tokenize(project_text)

        if not prompt_tokens or not project_tokens:
            return 0.0

        intersection = len(prompt_tokens.intersection(project_tokens))
        union = len(prompt_tokens.union(project_tokens))
        jaccard = intersection / max(union, 1)

        domain_bonus = 0.12 if project.domain and project.domain in prompt.lower() else 0.0
        return round(min(1.0, jaccard + domain_bonus), 4)
