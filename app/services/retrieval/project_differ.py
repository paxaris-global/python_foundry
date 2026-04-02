from typing import Optional

import re

from app.models.project import Project


class ProjectDiffer:
    @staticmethod
    def _tokenize(value: str) -> set[str]:
        return {token for token in re.findall(r"\w+", value.lower()) if len(token) > 2}

    def diff(self, base_project: Project, prompt: str, features: list[str], website_like: Optional[str]) -> dict:
        base_features = set((base_project.manifest or {}).get("features", []))
        target_features = {item.strip().lower() for item in features if item.strip()}

        prompt_tokens = self._tokenize(prompt)
        base_tokens = self._tokenize(base_project.description or "")

        return {
            "add_features": sorted(target_features - base_features),
            "keep_features": sorted(target_features.intersection(base_features)),
            "remove_features": sorted(base_features - target_features),
            "new_prompt_tokens": sorted(prompt_tokens - base_tokens)[:50],
            "website_like": website_like,
        }
