"""Pydantic schemas for onboarding structured outputs."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class OnboardingQuestionSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    question: str
    reason: str
    required: bool = True


class GenerateQuestionsModelResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    questions: list[OnboardingQuestionSchema] = Field(default_factory=list)


class NormalizedAgentConfigurationSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    business_profile: dict[str, Any] = Field(default_factory=dict)
    services: list[dict[str, Any]] = Field(default_factory=list)
    staff_members: list[dict[str, Any]] = Field(default_factory=list)
    working_hours: list[dict[str, Any]] = Field(default_factory=list)
    faqs: list[dict[str, Any]] = Field(default_factory=list)
    policies: list[str] = Field(default_factory=list)
    booking_rules: dict[str, Any] = Field(default_factory=dict)
    lead_qualification: dict[str, Any] = Field(default_factory=dict)
    handoff_rules: list[dict[str, Any]] = Field(default_factory=list)
    supported_languages: list[str] = Field(default_factory=list)
    default_language: str = "en"
    brand_tone: str = "professional, helpful"
    restricted_topics: list[str] = Field(default_factory=list)
    available_actions: list[str] = Field(default_factory=list)
    agent_rules: list[str] = Field(default_factory=list)


class BuildConfigurationModelResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent_configuration: NormalizedAgentConfigurationSchema
