from datetime import datetime
from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Shared type aliases – surfaced as enums in the OpenAPI spec
# ---------------------------------------------------------------------------

#: Lifecycle states of a generation job.
JobStatusValue = Literal["pending", "running", "completed", "failed"]

#: Execution mode chosen by the generation pipeline.
ExecutionModeValue = Literal["reuse", "adapt", "generate", "hybrid_scaffold"]

#: Connectivity state of a backing dependency.
DependencyState = Literal["up", "down"]


class APIMessage(BaseModel):
    """Generic single-message response."""

    message: str = Field(description="Human-readable message.")


class ErrorResponse(BaseModel):
    """Standard error payload returned by every non-2xx response.

    This shape is guaranteed across the whole API: request-body validation
    errors (422), not-found (404), service-unavailable (503) and internal
    errors (500) all return ``{"detail": "<message>"}``.
    """

    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {"detail": "Resource not found"},
            {"detail": "project_name: String should have at least 2 characters"},
            {"detail": "Service temporarily unavailable"},
        ]
    })

    detail: str = Field(
        description="Human-readable error description. For request-body "
        "validation errors, individual field messages are joined with '; '.",
    )


class TimestampedSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    created_at: datetime
    updated_at: datetime


class IDSchema(BaseModel):
    id: UUID


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class DependencyStatus(BaseModel):
    """Connectivity status of each backing service."""

    model_config = ConfigDict(json_schema_extra={
        "example": {"db": "up", "redis": "up", "chroma": "up"}
    })

    db: DependencyState = Field(description="PostgreSQL connectivity.")
    redis: DependencyState = Field(description="Redis (task queue / cache) connectivity.")
    chroma: DependencyState = Field(description="ChromaDB vector-store connectivity.")


class HealthCheckResponse(BaseModel):
    """Aggregated health check for the platform and its dependencies.

    The endpoint always returns HTTP 200; consult the ``status`` field to
    determine whether the platform is fully operational.
    """

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "status": "ok",
            "service": "ai-codegen-platform",
            "dependencies": {"db": "up", "redis": "up", "chroma": "up"},
        }
    })

    status: Literal["ok", "degraded"] = Field(
        description="Overall health. 'ok' when db and redis are both reachable; "
        "'degraded' otherwise. Chroma outages are reported but do not degrade overall status.",
    )
    service: str = Field(description="Service identifier.")
    dependencies: DependencyStatus = Field(description="Per-dependency connectivity status.")


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

class CacheEntryResponse(BaseModel):
    """Cached generation-fingerprint entry.

    Each entry maps a content fingerprint (hash of prompt + stack + features)
    to a previously generated project that can be reused.
    """

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "fingerprint": "sha256:abc123def456",
            "project_id": "c2f5b3e1-5678-1234-abcd-ef0123456789",
            "hit_count": 3,
            "request_payload": {"prompt": "Build a CRM", "backend": "springboot", "frontend": "angular", "features": ["authentication"]},
            "cache_metadata": {"domain": "crm", "execution_mode": "generate", "selection_score": 0.92},
            "created_at": "2025-06-01T12:00:00",
            "updated_at": "2025-06-01T12:01:00",
        }
    })

    fingerprint: str = Field(description="Content fingerprint (SHA-256 hash) that uniquely identifies this request.")
    project_id: Optional[str] = Field(default=None, description="UUID of the cached project. Null if the entry was created before a project was linked.")
    hit_count: int = Field(ge=0, description="Number of times this cache entry has been reused.")
    request_payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Original request parameters that produced this entry (prompt, backend, frontend, features).",
    )
    cache_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata captured at cache-write time (domain, execution_mode, selection_score).",
    )
    created_at: datetime = Field(description="Timestamp when the entry was created.")
    updated_at: datetime = Field(description="Timestamp of the most recent hit or update.")
