class ManifestBuilder:
    def build_manifest(self, project_spec: dict, api_contract: dict) -> dict:
        mandatory_files = [
            "backend/pom.xml",
            "backend/Dockerfile",
            "frontend/package.json",
            "frontend/Dockerfile",
            "frontend/nginx.conf",
            "docker-compose.yml",
            "README.md",
            ".env.example",
            "_meta/final_enriched_prompt.txt",
            "_meta/final_enriched_prompt.json",
        ]
        return {
            "project_name": project_spec["project_name"],
            "domain": project_spec.get("domain", "general"),
            "blueprint": project_spec.get("blueprint", {}).get("domain"),
            "backend": project_spec["backend"],
            "frontend": project_spec["frontend"],
            "features": project_spec["features"],
            "api_contract_summary": list(api_contract.get("paths", {}).keys()),
            "mandatory_files": mandatory_files,
        }
