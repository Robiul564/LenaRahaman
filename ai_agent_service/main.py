from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from apps.agent.views import router as agent_router
from apps.common.exceptions import ServiceError, ValidationServiceError, build_error_payload
from apps.common.middleware import RequestIDMiddleware
from apps.health.views import router as health_router
from apps.onboarding.views import router as onboarding_router
from core.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(
    title="AI Agent Service API",
    description="Stateless multi-tenant AI agent service for backend-driven messaging workflows.",
    version="1.0.0",
)
app.add_middleware(RequestIDMiddleware)


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


@app.exception_handler(ServiceError)
async def service_error_handler(request: Request, exc: ServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=build_error_payload(
            code=exc.code,
            message=exc.custom_message,
            details=exc.details,
            request_id=_request_id(request),
        ),
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    validation_error = ValidationServiceError(details=exc.errors())
    return JSONResponse(
        status_code=validation_error.status_code,
        content=build_error_payload(
            code=validation_error.code,
            message=validation_error.custom_message,
            details=validation_error.details,
            request_id=_request_id(request),
        ),
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled internal error", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content=build_error_payload(
            code="INTERNAL_SERVER_ERROR",
            message="Internal server error.",
            details=[],
            request_id=_request_id(request),
        ),
    )


app.include_router(health_router)
app.include_router(agent_router)
app.include_router(onboarding_router)
