"""FastAPI routes for AI agent message processing."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from apps.agent.serializers import ProcessMessageRequestSerializer, ProcessMessageResponseSerializer
from apps.agent.services.agent_service import AgentService
from apps.common.authentication import require_api_key
from apps.common.responses import success_payload
from apps.common.throttling import throttle

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])
agent_service = AgentService()


@router.post(
    "/process-message/",
    response_model=ProcessMessageResponseSerializer,
    dependencies=[Depends(require_api_key), Depends(throttle("agent_process"))],
)
async def process_message(request: Request, payload: ProcessMessageRequestSerializer) -> dict:
    request_id = getattr(request.state, "request_id", "")
    response_payload = agent_service.process_message(
        payload=payload.model_dump(),
        request_id=request_id,
    )
    return success_payload(response_payload, request_id=request_id)
