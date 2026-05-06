import json
from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.prompt_artifact import PromptArtifact
from app.utils.file_utils import ensure_directory, write_text_file

logger = get_logger(__name__)


class PromptDebugger:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    def persist_prompt_artifact(
        self,
        job_id: UUID,
        raw_user_prompt: str,
        parsed_prompt: dict,
        parsed_prompt_summary: dict,
        expanded_features: list[str],
        execution_mode: str,
        rag_summary: dict,
        rag_context_summary: dict,
        web_discovery_summary: dict,
        adaptation_context_summary: dict,
        trusted_sources: list[dict],
        pre_final_prompt: str | None,
        final_enriched_prompt: str,
        system_prompt: str | None,
    ) -> PromptArtifact:
        artifact = PromptArtifact(
            job_id=job_id,
            raw_user_prompt=raw_user_prompt,
            parsed_prompt=parsed_prompt,
            parsed_prompt_summary=parsed_prompt_summary,
            expanded_features=expanded_features,
            execution_mode=execution_mode,
            rag_summary=rag_summary,
            rag_context_summary=rag_context_summary,
            web_discovery_summary=web_discovery_summary,
            adaptation_context_summary=adaptation_context_summary,
            trusted_sources=trusted_sources,
            pre_final_prompt=pre_final_prompt,
            final_enriched_prompt=final_enriched_prompt,
            system_prompt=system_prompt,
        )
        self.db.add(artifact)
        self.db.commit()
        self.db.refresh(artifact)

        if self.settings.log_llm_prompts:
            clip = final_enriched_prompt[: min(len(final_enriched_prompt), self.settings.llm_prompt_log_max_chars)]
            logger.info(
                "FINAL_ENRICHED_PROMPT job_id=%s artifact_id=%s prompt=\"%s\"",
                str(job_id),
                str(artifact.id),
                clip.replace("\n", "\\n"),
            )

        # Also write the final enriched prompt to a well-known logs file for quick inspection
        try:
            if self.settings.log_llm_prompts:
                logs_dir = ensure_directory(Path(self.settings.base_dir) / "logs")
                log_path = logs_dir / "last_final_enriched_prompt.txt"
                write_text_file(log_path, final_enriched_prompt)
        except Exception:
            logger.debug("Failed to write final enriched prompt to logs file", exc_info=True)

        return artifact

    def write_project_prompt_files(self, project_root: Path, artifact: PromptArtifact, project_id: UUID) -> PromptArtifact:
        meta_dir = ensure_directory(project_root / "_meta")
        txt_path = meta_dir / "final_enriched_prompt.txt"
        json_path = meta_dir / "final_enriched_prompt.json"

        payload = {
            "job_id": str(artifact.job_id),
            "project_id": str(project_id),
            "raw_user_prompt": artifact.raw_user_prompt,
            "parsed_prompt": artifact.parsed_prompt,
            "parsed_prompt_summary": artifact.parsed_prompt_summary,
            "expanded_features": artifact.expanded_features,
            "execution_mode": artifact.execution_mode,
            "rag_summary": artifact.rag_summary,
            "rag_context_summary": artifact.rag_context_summary,
            "web_discovery_summary": artifact.web_discovery_summary,
            "adaptation_context_summary": artifact.adaptation_context_summary,
            "trusted_sources": artifact.trusted_sources,
            "pre_final_prompt": artifact.pre_final_prompt,
            "final_enriched_prompt": artifact.final_enriched_prompt,
            "system_prompt": artifact.system_prompt,
        }

        write_text_file(txt_path, artifact.final_enriched_prompt)
        write_text_file(json_path, json.dumps(payload, indent=2, ensure_ascii=False))

        artifact.project_id = project_id
        artifact.artifact_text_path = str(txt_path)
        artifact.artifact_json_path = str(json_path)
        self.db.commit()
        self.db.refresh(artifact)
        return artifact

    def get_by_job_id(self, job_id: UUID) -> PromptArtifact | None:
        return (
            self.db.query(PromptArtifact)
            .filter(PromptArtifact.job_id == job_id)
            .order_by(PromptArtifact.created_at.desc())
            .first()
        )
