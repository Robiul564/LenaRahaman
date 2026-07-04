from __future__ import annotations

from apps.onboarding.schemas import BuildConfigurationModelResponseSchema

URL = "/api/v1/onboarding/build-configuration/"


def test_build_configuration(api_client, auth_headers, mocker):
    mock_response = BuildConfigurationModelResponseSchema.model_validate(
        {
            "agent_configuration": {
                "business_profile": {
                    "business_name": "Example Clinic",
                    "business_type": "clinic",
                },
                "services": [
                    {
                        "service_id": "service_1",
                        "name": "General Consultation",
                        "price": 1000,
                        "currency": "BDT",
                    }
                ],
                "staff_members": [{"staff_id": "doctor_1", "name": "Dr. Rahman"}],
                "working_hours": [{"day": "monday", "open": "09:00", "close": "18:00"}],
                "faqs": [],
                "policies": ["Do not provide diagnosis."],
                "booking_rules": {"enabled": True},
                "lead_qualification": {"enabled": True, "required_fields": ["name", "phone"]},
                "handoff_rules": [{"condition": "human request", "department": "support"}],
                "supported_languages": ["en", "bn"],
                "default_language": "en",
                "brand_tone": "professional, warm",
                "restricted_topics": ["medical diagnosis"],
                "available_actions": ["check_availability", "create_booking", "handoff_to_human"],
                "agent_rules": ["Only use provided context."],
            }
        }
    )
    mocker.patch(
        "apps.agent.services.openai_client.OpenAIClientService.generate_structured_response",
        return_value=mock_response,
    )
    payload = {
        "business_id": "business_123",
        "business_type": "clinic",
        "onboarding_answers": {"business_name": "Example Clinic"},
    }
    response = api_client.post(URL, json=payload, headers=auth_headers)
    body = response.json()
    assert response.status_code == 200
    assert body["business_id"] == "business_123"
    assert body["agent_configuration"]["business_profile"]["business_type"] == "clinic"
