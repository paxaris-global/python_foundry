import time
from collections.abc import Callable

from app.core.logging import get_logger
from app.services.observability.metrics import track_stage

logger = get_logger(__name__)


class GenerationPipeline:
    def __init__(self) -> None:
        self.stage_timings: dict[str, float] = {}

    def execute_stage(
        self,
        stage: str,
        fn: Callable,
        progress_callback: Callable[[int, str], None] | None,
        progress: int,
        *args,
        **kwargs,
    ):
        if progress_callback:
            progress_callback(progress, stage)

        start = time.perf_counter()
        with track_stage(stage):
            result = fn(*args, **kwargs)
        elapsed = time.perf_counter() - start

        self.stage_timings[stage] = round(elapsed, 4)
        logger.info("stage=%s elapsed=%.4fs", stage, elapsed)
        return result
