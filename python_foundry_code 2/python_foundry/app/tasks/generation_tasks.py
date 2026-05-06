from celery import Task
from uuid import UUID

from sqlalchemy.exc import OperationalError

from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.models.job import Job, JobStatus
from app.services.generation.orchestrator import GenerationOrchestrator
from app.tasks.celery_app import celery_app
from app.utils.download_utils import copy_project_to_downloads

logger = get_logger(__name__)


@celery_app.task(
    bind=True,
    autoretry_for=(OperationalError, ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def generate_project_task(self: Task, job_id: str) -> dict:
    db = SessionLocal()
    try:
        job_uuid = UUID(job_id)
        job = db.query(Job).filter(Job.id == job_uuid).first()
        if not job:
            raise ValueError(f"Job not found: {job_id}")

        if job.status == JobStatus.completed and job.result_data:
            return job.result_data

        job.status = JobStatus.running
        job.progress = 1
        job.current_stage = "running"
        job.error = None
        db.commit()

        def progress_callback(progress: int, stage: str) -> None:
            job.progress = progress
            job.current_stage = stage
            existing = job.result_data or {}
            job.result_data = {**existing, "stage": stage}
            db.commit()

        orchestrator = GenerationOrchestrator(db=db)
        result = orchestrator.run(
            project_name=job.project_name,
            prompt=job.prompt,
            backend=job.backend,
            frontend=job.frontend,
            features=job.features,
            progress_callback=progress_callback,
            fingerprint=job.fingerprint,
            trace_id=job.trace_id,
            job_id=job.id,
            website_like=job.website_like,
            mode_preference=job.mode_preference,
        )

        job.status = JobStatus.completed
        job.progress = 100
        job.current_stage = "completed"
        job.project_id = UUID(result["project_id"])
        job.mode_selected = result.get("execution_mode")
        job.stage_timings = result.get("stage_timings", {})
        job.result_data = result
        db.commit()

        # Automatically download the project to Downloads folder
        try:
            zip_path = result.get("zip_path")
            if zip_path:
                download_path = copy_project_to_downloads(zip_path, job.project_name)
                logger.info(f"Project auto-downloaded to: {download_path}")
                # Store the download path in result_data for reference
                job.result_data["download_path"] = download_path
                db.commit()
        except Exception as exc:
            logger.error(f"Failed to auto-download project: {exc}")
            # Don't fail the entire job if download fails, just log it

        return result
    except Exception as exc:
        logger.exception("Generation task failed")
        db.rollback()
        job = db.query(Job).filter(Job.id == UUID(job_id)).first()
        if job:
            job.status = JobStatus.failed
            job.current_stage = "failed"
            job.error = str(exc)
            db.commit()
        raise
    finally:
        db.close()
