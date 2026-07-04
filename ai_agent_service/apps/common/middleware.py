"""Request ID middleware for FastAPI."""

from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class RequestIDMiddleware(BaseHTTPMiddleware):
    request_header = "X-Request-ID"
    response_header = "X-Request-ID"

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get(self.request_header) or str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers[self.response_header] = request_id
        return response


def get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "")
