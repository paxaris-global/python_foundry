class ProjectSpecBuilder:
    def build_project_spec(
        self,
        parsed_prompt: dict,
        project_name: str,
        backend: str,
        frontend: str,
        features: list[str],
    ) -> dict:
        clean_features = sorted(set(features + parsed_prompt.get("feature_hints", [])))
        package_suffix = project_name.replace("-", "").replace("_", "")
        package_suffix = "app" if not package_suffix else package_suffix.lower()

        application_class = "".join(part.title() for part in project_name.replace("_", "-").split("-")) or "GeneratedApp"

        return {
            "project_name": project_name,
            "description": parsed_prompt["summary"],
            "features": clean_features,
            "entities": parsed_prompt.get("entities") or ["customer"],
            "backend": {
                "stack": backend,
                "package": f"com.generated.{package_suffix}",
                "application_class": f"{application_class}Application",
            },
            "frontend": {
                "stack": frontend,
            },
        }
