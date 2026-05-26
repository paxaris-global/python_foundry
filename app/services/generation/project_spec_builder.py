from typing import Optional


class ProjectSpecBuilder:
    @staticmethod
    def _extract_labeled_value(prompt: str, label: str) -> Optional[str]:
        import re

        pattern = rf"(?im)^\s*[-*]?\s*{re.escape(label)}\s*:\s*([^\n\r]+)"
        match = re.search(pattern, prompt or "")
        if not match:
            return None
        value = match.group(1).strip().strip("`'\"")
        return value or None

    @staticmethod
    def _safe_repository_name(value: str) -> str:
        import re

        cleaned = re.sub(r"[^a-z0-9._-]+", "-", (value or "").strip().lower())
        cleaned = re.sub(r"-{2,}", "-", cleaned).strip("-._")
        return cleaned or "generated-app"

    @staticmethod
    def _safe_backend_description(raw_summary: str) -> str:
        # Keep OpenAPI description single-line and Java-string-safe.
        compact = " ".join((raw_summary or "").split())
        compact = compact.replace('"', "'")
        if not compact:
            return "Generated API for the requested application."
        return compact[:180]

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
        summary_lower = str(parsed_prompt.get("summary", "")).lower()
        ecommerce_hints = {"ecommerce", "e-commerce", "catalog", "cart", "checkout", "product", "wishlist"}
        if any(hint in summary_lower for hint in ecommerce_hints) or any(
            feature.lower() in ecommerce_hints for feature in clean_features
        ):
            # Keep ecommerce experiences in a storefront-oriented shell instead of
            # the default dashboard/workspace shell.
            layout_style = "landing"

        backend_repo_name = self._extract_labeled_value(
            parsed_prompt.get("summary", ""), "Backend repo name"
        ) or f"paxarisglobal-admin-{project_name}-backend"
        frontend_repo_name = self._extract_labeled_value(
            parsed_prompt.get("summary", ""), "Frontend repo name"
        ) or f"paxarisglobal-admin-{project_name}-frontend"

        return {
            "project_name": project_name,
            "description": self._safe_backend_description(parsed_prompt.get("summary", "")),
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
            "deployment": {
                "docker_org": "devopspaxarisglobalrepo",
                "backend_repo_name": self._safe_repository_name(backend_repo_name),
                "frontend_repo_name": self._safe_repository_name(frontend_repo_name),
            },
        }
