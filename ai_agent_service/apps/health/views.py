from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Request

from apps.common.responses import success_payload

router = APIRouter(prefix="/api/v1/health", tags=["health"])


@router.get("/")
async def health_check(request: Request) -> dict:
    payload = {
        "status": "ok",
        "service": "ai-agent-service",
        "timestamp": datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z"),
    }
    request_id = getattr(request.state, "request_id", None)
    return success_payload(payload, request_id=request_id)

