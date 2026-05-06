from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import DBSession
from app.core.logging import get_logger
from app.models.prompt_artifact import PromptArtifact
from app.services.generation.prompt_debugger import PromptDebugger

router = APIRouter(prefix="/debug", tags=["debug"])
logger = get_logger(__name__)


@router.get("/last-prompt")
def last_prompt(job_id: str | None = Query(default=None), db: DBSession = DBSession):
    """Return the last persisted final_enriched_prompt. If job_id is provided, return that job's latest artifact."""
    try:
        if job_id:
            artifact = PromptDebugger(db).get_by_job_id(UUID(job_id))
        else:
            artifact = (
                db.query(PromptArtifact).order_by(PromptArtifact.created_at.desc()).first()
            )
        if not artifact:
            return {"found": False, "message": "no prompt artifact found"}

        return {
            "found": True,
            "job_id": str(artifact.job_id),
            "artifact_id": str(artifact.id),
            "final_enriched_prompt": artifact.final_enriched_prompt,
            "artifact_text_path": artifact.artifact_text_path,
            "artifact_json_path": artifact.artifact_json_path,
        }
    except Exception as exc:
        logger.error("failed to fetch last prompt: %s", exc)
        return {"found": False, "error": str(exc)}
