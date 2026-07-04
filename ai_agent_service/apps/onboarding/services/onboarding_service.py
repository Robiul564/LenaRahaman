"""Service layer for onboarding endpoints."""

from __future__ import annotations

import logging
from typing import Any

from apps.agent.services.openai_client import OpenAIClientService
from apps.common.logging import log_event
from apps.onboarding.schemas import (
    BuildConfigurationModelResponseSchema,
    GenerateQuestionsModelResponseSchema,
)
from apps.onboarding.serializers import (
    BuildConfigurationResponseSerializer,
    GenerateQuestionsResponseSerializer,
)
from apps.onboarding.services.prompt_builder import OnboardingPromptBuilderService

logger = logging.getLogger(__name__)


class OnboardingService:
    def __init__(
        self,
        *,
        prompt_builder: OnboardingPromptBuilderService | None = None,
        openai_client: OpenAIClientService | None = None,
    ) -> None:
        self.prompt_builder = prompt_builder or OnboardingPromptBuilderService()
        self.openai_client = openai_client or OpenAIClientService()

    def generate_questions(self, payload: dict[str, Any], request_id: str) -> dict[str, Any]:
        business_id = payload["business_id"]
        messages = self.prompt_builder.build_generate_questions_messages(
            business_type=payload["business_type"],
            onboarding_data=payload.get("onboarding_data", {}),
            max_questions=payload.get("max_questions", 8),
            target_language=payload.get("target_language", "en"),
        )
        model_output = self.openai_client.generate_structured_response(
            messages=messages,
            schema_model=GenerateQuestionsModelResponseSchema,
            schema_name="onboarding_generate_questions",
        )
        response_payload = {
            "request_id": request_id,
            "business_id": business_id,
            "questions": model_output.model_dump().get("questions", []),
        }
        validated = GenerateQuestionsResponseSerializer.model_validate(response_payload)
        log_event(
            logger,
            "onboarding_questions_generated",
            request_id=request_id,
            business_id=business_id,
            question_count=len(response_payload["questions"]),
        )
        return validated.model_dump(mode="json")

    def build_configuration(self, payload: dict[str, Any], request_id: str) -> dict[str, Any]:
        business_id = payload["business_id"]
        messages = self.prompt_builder.build_configuration_messages(
            business_type=payload["business_type"],
            onboarding_answers=payload["onboarding_answers"],
        )
        model_output = self.openai_client.generate_structured_response(
            messages=messages,
            schema_model=BuildConfigurationModelResponseSchema,
            schema_name="onboarding_build_configuration",
        )
        response_payload = {
            "request_id": request_id,
            "business_id": business_id,
            "agent_configuration": model_output.model_dump().get("agent_configuration", {}),
        }
        validated = BuildConfigurationResponseSerializer.model_validate(response_payload)
        log_event(
            logger,
            "onboarding_configuration_built",
            request_id=request_id,
            business_id=business_id,
        )
        return validated.model_dump(mode="json")
