"""FastAPI authentication dependency for backend-to-service API key auth."""

from __future__ import annotations

import secrets

from fastapi import Header

from apps.common.exceptions import AuthenticationServiceError
from core.settings import get_settings


async def require_api_key(x_ai_service_key: str | None = Header(default=None)) -> str:
    settings = get_settings()
    expected = settings.ai_service_api_key

    if not x_ai_service_key:
        raise AuthenticationServiceError("Missing X-AI-Service-Key header.")

    if not expected:
        raise AuthenticationServiceError("AI service authentication is not configured.")

    if not secrets.compare_digest(x_ai_service_key, expected):
        raise AuthenticationServiceError("Invalid API key.")

    return "main-backend-service"
