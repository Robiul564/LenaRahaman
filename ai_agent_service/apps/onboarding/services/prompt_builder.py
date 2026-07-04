"""Prompt builders for onboarding tasks."""

from __future__ import annotations

import json
from typing import Any

from apps.onboarding.schemas import (
    BuildConfigurationModelResponseSchema,
    GenerateQuestionsModelResponseSchema,
)


class OnboardingPromptBuilderService:
    """Builds prompts for onboarding question generation and config normalization."""

    def build_generate_questions_messages(
        self,
        *,
        business_type: str,
        onboarding_data: dict[str, Any],
        max_questions: int,
        target_language: str,
    ) -> list[dict[str, str]]:
        schema_json = json.dumps(
            GenerateQuestionsModelResponseSchema.model_json_schema(mode="validation"),
            ensure_ascii=True,
            separators=(",", ":"),
        )
        data_json = json.dumps(onboarding_data, ensure_ascii=True, separators=(",", ":"))
        system_prompt = (
            "You generate missing onboarding questions for business AI agents. "
            "Ask only high-impact missing questions. "
            "Questions must be specific, actionable, and grouped by business needs.\n"
            "Return strict JSON only.\n"
            f"JSON schema: {schema_json}\n"
            f"Target language: {target_language}\n"
        )
        user_prompt = (
            f"Business type: {business_type}\n"
            f"Current onboarding data: {data_json}\n"
            f"Generate up to {max_questions} most important missing questions."
        )
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def build_configuration_messages(
        self,
        *,
        business_type: str,
        onboarding_answers: dict[str, Any],
    ) -> list[dict[str, str]]:
        schema_json = json.dumps(
            BuildConfigurationModelResponseSchema.model_json_schema(mode="validation"),
            ensure_ascii=True,
            separators=(",", ":"),
        )
        answers_json = json.dumps(onboarding_answers, ensure_ascii=True, separators=(",", ":"))
        system_prompt = (
            "You normalize onboarding answers into a production AI agent configuration. "
            "Do not invent facts. Preserve provided values and infer only safe defaults.\n"
            "Return strict JSON only.\n"
            f"JSON schema: {schema_json}\n"
        )
        user_prompt = (
            f"Business type: {business_type}\n"
            f"Onboarding answers: {answers_json}\n"
            "Build normalized agent configuration."
        )
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
