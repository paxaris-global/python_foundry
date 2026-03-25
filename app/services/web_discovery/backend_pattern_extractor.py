class BackendPatternExtractor:
    def extract(self, page_data: dict, repo_analysis: dict | None = None) -> list[str]:
        repo_analysis = repo_analysis or {}
        text = (page_data.get("text") or "").lower()

        patterns = []
        for token, label in [
            ("rest api", "rest_api"),
            ("jwt", "jwt_auth"),
            ("role", "rbac"),
            ("microservice", "microservice_split"),
            ("crud", "crud_service_layer"),
            ("queue", "async_jobs"),
        ]:
            if token in text:
                patterns.append(label)

        for hint in repo_analysis.get("architecture_hints", []):
            patterns.append(hint)

        return sorted(set(patterns))
