from typing import Optional

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.logging import get_logger

logger = get_logger(__name__)


def _format_validation_errors(errors: list[dict]) -> str:
    """Collapse Pydantic's error list into a single human-readable string."""
    parts: list[str] = []
    for err in errors:
        loc = ".".join(str(x) for x in err.get("loc", []) if x != "body")
        msg = err.get("msg", "invalid")
        parts.append(f"{loc}: {msg}" if loc else msg)
    return "; ".join(parts) or "Invalid request"


class AppException(Exception):
    status_code = 500
    detail = "Internal application error"

    def __init__(self, detail: Optional[str] = None):
        self.detail = detail or self.detail
        super().__init__(self.detail)


class NotFoundException(AppException):
    status_code = 404
    detail = "Resource not found"


class ValidationException(AppException):
    status_code = 422
    detail = "Validation error"


class GenerationException(AppException):
    status_code = 500
    detail = "Project generation failed"


class ServiceUnavailableException(AppException):
    status_code = 503
    detail = "Service temporarily unavailable"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def handle_app_exception(request: Request, exc: AppException) -> JSONResponse:
        logger.warning(
            "AppException: status=%d detail=%s path=%s",
            exc.status_code, exc.detail, request.url.path,
        )
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Normalise FastAPI's default {"detail": [{loc, msg, type}, ...]} into our
        # standard {"detail": str} contract so all 422 responses have the same shape.
        detail = _format_validation_errors(exc.errors())
        logger.warning("RequestValidationError: path=%s detail=%s", request.url.path, detail)
        return JSONResponse(status_code=422, content={"detail": detail})

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "Unhandled exception on %s %s", request.method, request.url.path,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected internal error occurred. Please try again later."},
        )
