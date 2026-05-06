class RepoAnalyzer:
    def analyze(self, repo_data: dict) -> dict:
        readme = (repo_data.get("readme") or "").lower()
        metadata = repo_data.get("metadata") or {}

        stack_hints = []
        for keyword, hint in [
            ("spring boot", "springboot"),
            ("angular", "angular"),
            ("react", "react"),
            ("docker", "docker"),
            ("postgres", "postgres"),
        ]:
            if keyword in readme:
                stack_hints.append(hint)

        architecture_hints = []
        for token in ["controller", "service", "repository", "dto", "entity", "clean architecture"]:
            if token in readme:
                architecture_hints.append(token)

        return {
            "stars": metadata.get("stargazers_count", 0),
            "forks": metadata.get("forks_count", 0),
            "stack_hints": sorted(set(stack_hints)),
            "architecture_hints": sorted(set(architecture_hints)),
        }
