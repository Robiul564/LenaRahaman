"""Response helper functions for FastAPI endpoints."""

from __future__ import annotations

from typing import Any


def success_payload(payload: dict[str, Any], request_id: str | None = None) -> dict[str, Any]:
    body = dict(payload)
    if request_id and "request_id" not in body:
        body["request_id"] = request_id
    return body
