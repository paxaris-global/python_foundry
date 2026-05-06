from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    status_code = 500
    detail = "Internal application error"

    def __init__(self, detail: str | None = None):
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


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def handle_app_exception(_: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=500, content={"detail": str(exc)})
