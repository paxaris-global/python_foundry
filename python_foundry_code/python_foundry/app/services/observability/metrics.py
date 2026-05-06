import time
from contextlib import contextmanager

from prometheus_client import Counter, Histogram

GENERATION_COUNTER = Counter("codegen_generation_total", "Total generation requests", ["status"])
CACHE_COUNTER = Counter("codegen_cache_total", "Cache outcome counter", ["outcome"])
STAGE_HISTOGRAM = Histogram("codegen_stage_seconds", "Pipeline stage latency", ["stage"])
RAG_HISTOGRAM = Histogram("codegen_rag_seconds", "RAG retrieval latency")


@contextmanager
def track_stage(stage: str):
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        STAGE_HISTOGRAM.labels(stage=stage).observe(elapsed)
