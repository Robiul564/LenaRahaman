from __future__ import annotations

import uuid

from apps.agent.schemas import AgentModelResponseSchema
from apps.common.exceptions import OpenAIInvalidResponseError, OpenAIServiceError

PROCESS_MESSAGE_URL = "/api/v1/agent/process-message/"


def build_model_response() -> AgentModelResponseSchema:
    return AgentModelResponseSchema.model_validate(
        {
            "reply_message": "I can help with that. What time do you prefer tomorrow?",
            "reply_language": "en",
            "intent": {"name": "booking_request", "confidence": 0.95},
            "conversation_state": {
                "status": "active",
                "current_flow": "booking",
                "next_required_information": ["preferred_time"],
            },
            "extracted_data": {
                "customer": {
                    "name": None,
                    "phone": None,
                    "email": None,
                    "language": "en",
                },
                "lead": {
                    "service_interest": "General Consultation",
                    "budget": None,
                    "preferred_date": "2026-07-03",
                    "preferred_time": None,
                    "notes": "Customer wants an appointment tomorrow.",
                },
            },
            "actions": [
                {
                    "action_id": str(uuid.uuid4()),
                    "type": "check_availability",
                    "priority": "normal",
                    "data": {"service_id": "service_1", "requested_date": "2026-07-03"},
                    "requires_backend_result": True,
                }
            ],
            "handoff": {"required": False, "department": None, "priority": None, "reason": None},
            "safety": {"flagged": False, "category": None, "instructions": None},
            "internal_summary": "Customer asked to book a consultation tomorrow.",
        }
    )


def _is_valid_uuid(raw_value: str) -> bool:
    try:
        uuid.UUID(raw_value)
        return True
    except ValueError:
        return False


def test_api_key_authentication_required(api_client, process_message_payload):
    response = api_client.post(PROCESS_MESSAGE_URL, json=process_message_payload)
    body = response.json()
    assert response.status_code == 401
    assert body["error"]["code"] == "AUTHENTICATION_FAILED"


def test_invalid_request_validation(api_client, auth_headers, process_message_payload):
    invalid_payload = dict(process_message_payload)
    invalid_payload.pop("business_id")
    response = api_client.post(PROCESS_MESSAGE_URL, json=invalid_payload, headers=auth_headers)
    body = response.json()
    assert response.status_code == 400
    assert body["error"]["code"] == "VALIDATION_ERROR"


def test_valid_message_processing(api_client, auth_headers, process_message_payload, mocker):
    process_message_payload["business_context"]["working_hours"] = [
        {"day": "friday", "open": "09:00", "close": "18:00"}
    ]
    mocker.patch(
        "apps.agent.services.openai_client.OpenAIClientService.generate_structured_response",
        return_value=build_model_response(),
    )
    response = api_client.post(
        PROCESS_MESSAGE_URL, json=process_message_payload, headers=auth_headers
    )
    body = response.json()
    assert response.status_code == 200
    assert body["business_id"] == "business_123"
    assert body["intent"]["name"] == "booking_request"
    assert body["actions"][0]["type"] == "check_availability"


def test_openai_api_failure(api_client, auth_headers, process_message_payload, mocker):
    mocker.patch(
        "apps.agent.services.openai_client.OpenAIClientService.generate_structured_response",
        side_effect=OpenAIServiceError("OpenAI provider unavailable."),
    )
    response = api_client.post(
        PROCESS_MESSAGE_URL, json=process_message_payload, headers=auth_headers
    )
    body = response.json()
    assert response.status_code == 502
    assert body["error"]["code"] == "OPENAI_API_ERROR"


def test_invalid_openai_json_response(api_client, auth_headers, process_message_payload, mocker):
    mocker.patch(
        "apps.agent.services.openai_client.OpenAIClientService.generate_structured_response",
        side_effect=OpenAIInvalidResponseError("Invalid response payload."),
    )
    response = api_client.post(
        PROCESS_MESSAGE_URL, json=process_message_payload, headers=auth_headers
    )
    body = response.json()
    assert response.status_code == 502
    assert body["error"]["code"] == "OPENAI_INVALID_RESPONSE"


def test_unsupported_action_validation(api_client, auth_headers, process_message_payload, mocker):
    model_response = build_model_response()
    data = model_response.model_dump()
    data["actions"] = [
        {
            "action_id": str(uuid.uuid4()),
            "type": "create_booking",
            "priority": "normal",
            "data": {},
            "requires_backend_result": True,
        }
    ]
    model_response = AgentModelResponseSchema.model_validate(data)
    process_message_payload["available_actions"] = ["send_message", "handoff_to_human"]
    mocker.patch(
        "apps.agent.services.openai_client.OpenAIClientService.generate_structured_response",
        return_value=model_response,
    )
    response = api_client.post(
        PROCESS_MESSAGE_URL, json=process_message_payload, headers=auth_headers
    )
    body = response.json()
    assert response.status_code == 200
    assert body["handoff"]["required"] is True
    assert all(action["type"] != "create_booking" for action in body["actions"])
    assert any(action["type"] == "handoff_to_human" for action in body["actions"])


def test_business_id_isolation_preserved(api_client, auth_headers, process_message_payload, mocker):
    process_message_payload["business_id"] = "business_isolated_001"
    mocker.patch(
        "apps.agent.services.openai_client.OpenAIClientService.generate_structured_response",
        return_value=build_model_response(),
    )
    response = api_client.post(
        PROCESS_MESSAGE_URL, json=process_message_payload, headers=auth_headers
    )
    body = response.json()
    assert response.status_code == 200
    assert body["business_id"] == "business_isolated_001"


def test_emergency_handoff_behavior(api_client, auth_headers, process_message_payload, mocker):
    process_message_payload["message"]["text"] = "This is an emergency, I have severe chest pain."
    mocker.patch(
        "apps.agent.services.openai_client.OpenAIClientService.generate_structured_response",
        return_value=build_model_response(),
    )
    response = api_client.post(
        PROCESS_MESSAGE_URL, json=process_message_payload, headers=auth_headers
    )
    body = response.json()
    assert response.status_code == 200
    assert body["handoff"]["required"] is True
    assert body["handoff"]["priority"] == "urgent"
    assert body["safety"]["flagged"] is True


def test_action_id_is_normalized_to_uuid(api_client, auth_headers, process_message_payload, mocker):
    process_message_payload["business_context"]["working_hours"] = [
        {"day": "friday", "open": "09:00", "close": "18:00"}
    ]

    model_response = build_model_response()
    response_payload = model_response.model_dump()
    response_payload["actions"][0]["action_id"] = "check_availability_001"

    mocker.patch(
        "apps.agent.services.openai_client.OpenAIClientService.generate_structured_response",
        return_value=AgentModelResponseSchema.model_validate(response_payload),
    )

    response = api_client.post(
        PROCESS_MESSAGE_URL, json=process_message_payload, headers=auth_headers
    )
    body = response.json()

    assert response.status_code == 200
    assert _is_valid_uuid(body["actions"][0]["action_id"])


def test_check_availability_window_is_clamped_to_working_hours(
    api_client, auth_headers, process_message_payload, mocker
):
    process_message_payload["business_context"]["working_hours"] = [
        {"day": "friday", "open": "09:00", "close": "13:00"}
    ]

    model_response = build_model_response()
    response_payload = model_response.model_dump()
    response_payload["actions"] = [
        {
            "action_id": "check_availability_001",
            "type": "check_availability",
            "priority": "normal",
            "data": {
                "service_id": "service_1",
                "date": "2026-07-03",
                "time_range_start": "12:00",
                "time_range_end": "18:00",
            },
            "requires_backend_result": True,
        }
    ]

    mocker.patch(
        "apps.agent.services.openai_client.OpenAIClientService.generate_structured_response",
        return_value=AgentModelResponseSchema.model_validate(response_payload),
    )

    response = api_client.post(
        PROCESS_MESSAGE_URL, json=process_message_payload, headers=auth_headers
    )
    body = response.json()

    assert response.status_code == 200
    action_data = body["actions"][0]["data"]
    assert action_data["time_range_start"] == "12:00"
    assert action_data["time_range_end"] == "13:00"
    assert "Adjusted requested booking time window" in body["internal_summary"]


def test_check_availability_removed_for_non_working_day(
    api_client, auth_headers, process_message_payload, mocker
):
    process_message_payload["business_context"]["working_hours"] = [
        {"day": "monday", "open": "09:00", "close": "18:00"}
    ]

    model_response = build_model_response()
    response_payload = model_response.model_dump()
    response_payload["actions"] = [
        {
            "action_id": "check_availability_001",
            "type": "check_availability",
            "priority": "normal",
            "data": {
                "service_id": "service_1",
                "date": "2026-07-03",
                "time_range_start": "12:00",
                "time_range_end": "18:00",
            },
            "requires_backend_result": True,
        }
    ]

    mocker.patch(
        "apps.agent.services.openai_client.OpenAIClientService.generate_structured_response",
        return_value=AgentModelResponseSchema.model_validate(response_payload),
    )

    response = api_client.post(
        PROCESS_MESSAGE_URL, json=process_message_payload, headers=auth_headers
    )
    body = response.json()

    assert response.status_code == 200
    assert body["actions"] == []
    assert "closed on that day" in body["reply_message"].lower()
    assert "preferred_date" in body["conversation_state"]["next_required_information"]
