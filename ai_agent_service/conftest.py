from __future__ import annotations

import copy
import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def service_settings():
    os.environ["AI_SERVICE_API_KEY"] = "test-ai-service-key"
    os.environ["OPENAI_API_KEY"] = "test-openai-key"
    os.environ["OPENAI_MODEL"] = "gpt-4.1-mini"
    os.environ["AGENT_RATE_LIMIT"] = "10000/min"
    os.environ["ONBOARDING_RATE_LIMIT"] = "10000/min"
    os.environ["CONFIGURATION_RATE_LIMIT"] = "10000/min"

    from core.settings import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def api_client() -> TestClient:
    from main import app

    return TestClient(app)


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"X-AI-Service-Key": "test-ai-service-key"}


@pytest.fixture
def process_message_payload() -> dict:
    payload = {
        "business_id": "business_123",
        "channel": "whatsapp",
        "customer": {
            "customer_id": "customer_456",
            "name": "John Doe",
            "phone": "+8801712345678",
            "language": "en",
        },
        "message": {
            "message_id": "message_789",
            "text": "I want to book an appointment tomorrow.",
            "message_type": "text",
            "timestamp": "2026-07-02T10:00:00Z",
        },
        "business_context": {
            "business_name": "Example Clinic",
            "business_type": "clinic",
            "business_description": "A healthcare clinic providing consultations.",
            "timezone": "Asia/Dhaka",
            "supported_languages": ["en", "bn"],
            "default_language": "en",
            "brand_tone": "professional, warm, helpful",
            "services": [
                {
                    "service_id": "service_1",
                    "name": "General Consultation",
                    "description": "Consultation with a general physician.",
                    "price": 1000,
                    "currency": "BDT",
                    "duration_minutes": 30,
                    "booking_required": True,
                }
            ],
            "staff_members": [
                {
                    "staff_id": "doctor_1",
                    "name": "Dr. Rahman",
                    "role": "General Physician",
                    "services": ["service_1"],
                }
            ],
            "working_hours": [{"day": "monday", "open": "09:00", "close": "18:00"}],
            "booking": {
                "enabled": True,
                "booking_method": "calendar_api",
                "requires_confirmation": True,
                "cancellation_policy": (
                    "Cancellation is allowed up to 2 hours "
                    "before the appointment."
                ),
            },
            "faqs": [
                {
                    "question": "Do you accept walk-ins?",
                    "answer": "Walk-ins are accepted based on availability.",
                }
            ],
            "policies": [
                "Do not provide medical diagnosis.",
                "Do not provide emergency medical advice.",
                "Ask the customer to contact emergency services for emergencies.",
            ],
            "lead_qualification": {
                "enabled": True,
                "required_fields": ["name", "phone", "service_interest"],
                "optional_fields": ["budget", "preferred_time"],
            },
            "handoff_rules": [
                {
                    "condition": "customer requests human support",
                    "department": "support",
                    "priority": "normal",
                },
                {
                    "condition": "medical emergency or urgent medical issue",
                    "department": "emergency",
                    "priority": "urgent",
                },
            ],
            "agent_rules": [
                "Never invent pricing, availability, staff information, or policies.",
                "Only use information provided in business_context.",
                "Ask a clarification question if required information is missing.",
                "Use the customer preferred language when possible.",
            ],
        },
        "conversation_history": [
            {
                "role": "customer",
                "content": "Hello, I need an appointment.",
                "timestamp": "2026-07-02T09:55:00Z",
            },
            {
                "role": "assistant",
                "content": "Sure. Which service do you need?",
                "timestamp": "2026-07-02T09:56:00Z",
            },
        ],
        "available_actions": [
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
        ],
        "backend_action_results": [],
    }
    return copy.deepcopy(payload)
