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

RETRYABLE_EXCEPTIONS = (OperationalError, ConnectionError, TimeoutError)


def _mark_job_failed(db, job_id: str, error_message: str) -> None:
    """Reload the job in a clean state and mark it as failed."""
    try:
        db.rollback()
        job = db.query(Job).filter(Job.id == UUID(job_id)).first()
        if job:
            job.status = JobStatus.failed
            job.current_stage = "failed"
            job.error = error_message
            db.commit()
            logger.info("[celery] job=%s marked as failed: %s", job_id, error_message)
    except Exception:
        logger.exception("[celery] Failed to mark job=%s as failed in database", job_id)


@celery_app.task(
    bind=True,
    autoretry_for=RETRYABLE_EXCEPTIONS,
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def generate_project_task(self: Task, job_id: str) -> dict:
    logger.info("[celery] generate_project_task received job_id=%s task_id=%s retry=%s",
                job_id, self.request.id, self.request.retries)
    db = SessionLocal()
    try:
        job_uuid = UUID(job_id)
        job = db.query(Job).filter(Job.id == job_uuid).first()
        logger.info("[celery] job loaded: %s status=%s", job_id, job.status if job else "NOT_FOUND")
        if not job:
            logger.error("[celery] Job not found in database: %s", job_id)
            raise ValueError(f"Job not found: {job_id}")

        if job.status == JobStatus.completed and job.result_data:
            logger.info("[celery] job=%s already completed, returning cached result", job_id)
            return job.result_data

        job.status = JobStatus.running
        job.progress = 1
        job.current_stage = "running"
        job.error = None
        db.commit()

        def progress_callback(progress: int, stage: str) -> None:
            try:
                job.progress = progress
                job.current_stage = stage
                existing = job.result_data or {}
                job.result_data = {**existing, "stage": stage}
                db.commit()
            except Exception:
                logger.warning("[celery] Failed to update progress for job=%s stage=%s", job_id, stage)
                db.rollback()

        logger.info("[celery] invoking GenerationOrchestrator.run for job=%s", job_id)
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
        logger.info("[celery] job=%s completed successfully", job_id)

        try:
            zip_path = result.get("zip_path")
            if zip_path:
                download_path = copy_project_to_downloads(zip_path, job.project_name)
                logger.info("Project auto-downloaded to: %s", download_path)
                job.result_data = {**job.result_data, "download_path": download_path}
                db.commit()
        except Exception:
            logger.warning("[celery] Failed to auto-download project for job=%s", job_id, exc_info=True)

        return result

    except RETRYABLE_EXCEPTIONS as exc:
        retries = self.request.retries
        max_retries = self.retry_kwargs.get("max_retries", 3)
        logger.warning(
            "[celery] Retryable error for job=%s (attempt %d/%d): %s",
            job_id, retries + 1, max_retries, type(exc).__name__,
        )
        if retries >= max_retries:
            _mark_job_failed(db, job_id, f"Failed after {max_retries} retries: {type(exc).__name__}")
        raise

    except Exception as exc:
        logger.exception("[celery] Generation task failed permanently for job=%s", job_id)
        _mark_job_failed(db, job_id, str(exc)[:500])
        raise

    finally:
        db.close()
