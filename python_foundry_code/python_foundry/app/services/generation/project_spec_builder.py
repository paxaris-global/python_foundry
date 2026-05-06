class ProjectSpecBuilder:
    @staticmethod
    def _theme_tokens(ui_profile: str) -> dict:
        palettes = {
            "professional": {
                "primary": "#2563eb",
                "accent": "#14b8a6",
                "background": "#f3f6fb",
                "surface": "#ffffff",
                "text": "#0f172a",
                "muted": "#475569",
            },
            "minimal": {
                "primary": "#334155",
                "accent": "#64748b",
                "background": "#f8fafc",
                "surface": "#ffffff",
                "text": "#0f172a",
                "muted": "#64748b",
            },
            "luxury": {
                "primary": "#6d28d9",
                "accent": "#d97706",
                "background": "#160b2b",
                "surface": "#24123f",
                "text": "#f8fafc",
                "muted": "#d6bcfa",
            },
            "vibrant": {
                "primary": "#7c3aed",
                "accent": "#ec4899",
                "background": "#f5f3ff",
                "surface": "#ffffff",
                "text": "#1e1b4b",
                "muted": "#6d28d9",
            },
        }
        return palettes.get(ui_profile, palettes["professional"])

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
        ui_profile = parsed_prompt.get("ui_profile", "professional")
        layout_style = parsed_prompt.get("layout_style", "workspace")
        brand_tone = parsed_prompt.get("brand_tone", "professional")

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
                "ui_profile": ui_profile,
                "layout_style": layout_style,
                "brand_tone": brand_tone,
                "visual_keywords": parsed_prompt.get("visual_keywords", []),
                "theme_tokens": self._theme_tokens(ui_profile),
            },
        }
