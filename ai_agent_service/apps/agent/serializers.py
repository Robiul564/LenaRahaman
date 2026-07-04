"""Pydantic request/response models for agent APIs."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CustomerSerializer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_id: str = Field(min_length=1, max_length=128)
    name: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=32)
    language: str | None = Field(default=None, max_length=10)


class MessageSerializer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message_id: str = Field(min_length=1, max_length=128)
    text: str = Field(min_length=1)
    message_type: str = Field(min_length=1, max_length=32)
    timestamp: datetime


class ServiceItemSerializer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service_id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    price: float | None = None
    currency: str | None = Field(default=None, max_length=16)
    duration_minutes: int | None = Field(default=None, ge=0)
    booking_required: bool = False


class StaffMemberSerializer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    staff_id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=255)
    role: str | None = Field(default=None, max_length=255)
    services: list[str] = Field(default_factory=list)


class WorkingHourSerializer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    day: Literal[
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    ]
    open: str = Field(pattern=r"^\d{2}:\d{2}$")
    close: str = Field(pattern=r"^\d{2}:\d{2}$")


class BookingConfigSerializer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    booking_method: str | None = Field(default=None, max_length=64)
    requires_confirmation: bool = False
    cancellation_policy: str | None = None


class FAQSerializer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str
    answer: str


class LeadQualificationSerializer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    required_fields: list[str] = Field(default_factory=list)
    optional_fields: list[str] = Field(default_factory=list)


class HandoffRuleSerializer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    condition: str
    department: str
    priority: Literal["low", "normal", "high", "urgent"] = "normal"


class BusinessContextSerializer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    business_name: str
    business_type: str
    business_description: str | None = None
    timezone: str = "UTC"
    supported_languages: list[str] = Field(default_factory=list)
    default_language: str = "en"
    brand_tone: str | None = None
    services: list[ServiceItemSerializer] = Field(default_factory=list)
    staff_members: list[StaffMemberSerializer] = Field(default_factory=list)
    working_hours: list[WorkingHourSerializer] = Field(default_factory=list)
    booking: BookingConfigSerializer = Field(default_factory=BookingConfigSerializer)
    faqs: list[FAQSerializer] = Field(default_factory=list)
    policies: list[str] = Field(default_factory=list)
    lead_qualification: LeadQualificationSerializer = Field(
        default_factory=LeadQualificationSerializer
    )
    handoff_rules: list[HandoffRuleSerializer] = Field(default_factory=list)
    agent_rules: list[str] = Field(default_factory=list)


class ConversationItemSerializer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["customer", "assistant", "system"]
    content: str
    timestamp: datetime | None = None


class BackendActionResultSerializer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action_id: str
    type: str
    success: bool
    data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class ProcessMessageRequestSerializer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    business_id: str
    channel: str = "whatsapp"
    customer: CustomerSerializer
    message: MessageSerializer
    business_context: BusinessContextSerializer
    conversation_history: list[ConversationItemSerializer] = Field(default_factory=list)
    available_actions: list[str] = Field(min_length=1)
    backend_action_results: list[BackendActionResultSerializer] = Field(default_factory=list)

    @field_validator("business_id")
    @classmethod
    def validate_business_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("business_id is required for tenant isolation.")
        return value


class IntentResponseSerializer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    confidence: float = Field(ge=0.0, le=1.0)


class ConversationStateResponseSerializer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    current_flow: str | None = None
    next_required_information: list[str] = Field(default_factory=list)


class ExtractedCustomerSerializer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    phone: str | None = None
    email: str | None = None
    language: str | None = None


class ExtractedLeadSerializer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service_interest: str | None = None
    budget: str | None = None
    preferred_date: str | None = None
    preferred_time: str | None = None
    notes: str | None = None


class ExtractedDataResponseSerializer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer: ExtractedCustomerSerializer
    lead: ExtractedLeadSerializer


class ActionResponseSerializer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action_id: str
    type: str
    priority: Literal["low", "normal", "high", "urgent"] = "normal"
    data: dict[str, Any] = Field(default_factory=dict)
    requires_backend_result: bool = False


class HandoffResponseSerializer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    required: bool = False
    department: str | None = None
    priority: str | None = None
    reason: str | None = None


class SafetyResponseSerializer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    flagged: bool = False
    category: str | None = None
    instructions: str | None = None


class ProcessMessageResponseSerializer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    business_id: str
    reply_message: str
    reply_language: str
    intent: IntentResponseSerializer
    conversation_state: ConversationStateResponseSerializer
    extracted_data: ExtractedDataResponseSerializer
    actions: list[ActionResponseSerializer]
    handoff: HandoffResponseSerializer
    safety: SafetyResponseSerializer
    internal_summary: str
