"""Common service exceptions and error payload helpers."""

from __future__ import annotations

from typing import Any


class ServiceError(Exception):
    code = "INTERNAL_SERVER_ERROR"
    message = "An unexpected error occurred."
    status_code = 500

    def __init__(self, message: str | None = None, details: list[Any] | None = None):
        super().__init__(message or self.message)
        self.custom_message = message or self.message
        self.details = details or []


class AuthenticationServiceError(ServiceError):
    code = "AUTHENTICATION_FAILED"
    message = "Authentication failed."
    status_code = 401


class ValidationServiceError(ServiceError):
    code = "VALIDATION_ERROR"
    message = "Invalid request payload."
    status_code = 400


class OpenAIServiceError(ServiceError):
    code = "OPENAI_API_ERROR"
    message = "OpenAI API request failed."
    status_code = 502


class OpenAIInvalidResponseError(ServiceError):
    code = "OPENAI_INVALID_RESPONSE"
    message = "OpenAI returned an invalid response."
    status_code = 502


class UnsupportedActionError(ServiceError):
    code = "UNSUPPORTED_ACTION"
    message = "The AI requested an action that is unavailable."
    status_code = 400


class RateLimitedServiceError(ServiceError):
    code = "RATE_LIMITED"
    message = "Too many requests. Try again later."
    status_code = 429


def build_error_payload(
    *,
    code: str,
    message: str,
    details: list[Any] | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
            "details": details or [],
        }
    }
    if request_id:
        payload["request_id"] = request_id
    return payload
