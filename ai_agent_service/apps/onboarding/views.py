"""FastAPI routes for onboarding helper endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from apps.common.authentication import require_api_key
from apps.common.responses import success_payload
from apps.common.throttling import throttle
from apps.onboarding.serializers import (
    BuildConfigurationRequestSerializer,
    BuildConfigurationResponseSerializer,
    GenerateQuestionsRequestSerializer,
    GenerateQuestionsResponseSerializer,
)
from apps.onboarding.services.onboarding_service import OnboardingService

router = APIRouter(prefix="/api/v1/onboarding", tags=["onboarding"])
onboarding_service = OnboardingService()


@router.post(
    "/generate-questions/",
    response_model=GenerateQuestionsResponseSerializer,
    dependencies=[Depends(require_api_key), Depends(throttle("onboarding_questions"))],
)
async def generate_questions(request: Request, payload: GenerateQuestionsRequestSerializer) -> dict:
    request_id = getattr(request.state, "request_id", "")
    response_payload = onboarding_service.generate_questions(
        payload=payload.model_dump(), request_id=request_id
    )
    return success_payload(response_payload, request_id=request_id)


@router.post(
    "/build-configuration/",
    response_model=BuildConfigurationResponseSerializer,
    dependencies=[Depends(require_api_key), Depends(throttle("onboarding_configuration"))],
)
async def build_configuration(
    request: Request, payload: BuildConfigurationRequestSerializer
) -> dict:
    request_id = getattr(request.state, "request_id", "")
    response_payload = onboarding_service.build_configuration(
        payload=payload.model_dump(), request_id=request_id
    )
    return success_payload(response_payload, request_id=request_id)
