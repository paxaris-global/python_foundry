from app.models.project import Project


class ProjectAdapter:
    def build_adaptation_context(self, base_project: Project, diff_summary: dict) -> dict:
        return {
            "base_project_id": str(base_project.id),
            "base_project_name": base_project.name,
            "base_project_domain": base_project.domain,
            "base_project_blueprint": base_project.blueprint_used,
            "base_project_path": base_project.project_path,
            "base_project_manifest": base_project.manifest,
            "adaptation_diff": diff_summary,
        }
