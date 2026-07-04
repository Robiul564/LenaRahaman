"""Pydantic schemas for validating model structured outputs."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

SUPPORTED_INTENTS = [
    "greeting",
    "faq",
    "service_inquiry",
    "pricing_inquiry",
    "booking_request",
    "booking_confirmation",
    "booking_cancellation",
    "booking_reschedule",
    "availability_request",
    "lead_capture",
    "lead_qualification",
    "order_tracking",
    "payment_request",
    "refund_request",
    "complaint",
    "human_handoff",
    "business_hours",
    "location_request",
    "staff_request",
    "unknown",
]

SUPPORTED_ACTION_TYPES = [
    "send_message",
    "create_lead",
    "update_lead",
    "check_availability",
    "create_booking",
    "cancel_booking",
    "reschedule_booking",
    "handoff_to_human",
    "notify_business_owner",
    "create_support_ticket",
    "request_payment_link",
    "track_order",
]


class IntentSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(default="unknown")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ConversationStateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = "active"
    current_flow: str | None = None
    next_required_information: list[str] = Field(default_factory=list)


class ExtractedCustomerSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    phone: str | None = None
    email: str | None = None
    language: str | None = None


class ExtractedLeadSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service_interest: str | None = None
    budget: str | None = None
    preferred_date: str | None = None
    preferred_time: str | None = None
    notes: str | None = None


class ExtractedDataSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer: ExtractedCustomerSchema = Field(default_factory=ExtractedCustomerSchema)
    lead: ExtractedLeadSchema = Field(default_factory=ExtractedLeadSchema)


class ActionSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action_id: str
    type: str
    priority: str = "normal"
    data: dict[str, Any] = Field(default_factory=dict)
    requires_backend_result: bool = False


class HandoffSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    required: bool = False
    department: str | None = None
    priority: str | None = None
    reason: str | None = None


class SafetySchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    flagged: bool = False
    category: str | None = None
    instructions: str | None = None


class AgentModelResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reply_message: str
    reply_language: str
    intent: IntentSchema
    conversation_state: ConversationStateSchema
    extracted_data: ExtractedDataSchema
    actions: list[ActionSchema] = Field(default_factory=list)
    handoff: HandoffSchema = Field(default_factory=HandoffSchema)
    safety: SafetySchema = Field(default_factory=SafetySchema)
    internal_summary: str
