"""Pydantic request/response models for onboarding APIs."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class GenerateQuestionsRequestSerializer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    business_id: str = Field(min_length=1, max_length=128)
    business_type: str = Field(min_length=1, max_length=128)
    onboarding_data: dict[str, Any] = Field(default_factory=dict)
    max_questions: int = Field(default=8, ge=1, le=15)
    target_language: str = Field(default="en", max_length=10)


class OnboardingQuestionSerializer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str = Field(max_length=128)
    question: str
    reason: str
    required: bool = True


class GenerateQuestionsResponseSerializer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    business_id: str
    questions: list[OnboardingQuestionSerializer]


class BuildConfigurationRequestSerializer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    business_id: str = Field(min_length=1, max_length=128)
    business_type: str = Field(min_length=1, max_length=128)
    onboarding_answers: dict[str, Any]


class BuildConfigurationResponseSerializer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    business_id: str
    agent_configuration: dict[str, Any]
