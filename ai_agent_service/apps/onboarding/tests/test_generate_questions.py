from __future__ import annotations

from apps.onboarding.schemas import GenerateQuestionsModelResponseSchema

URL = "/api/v1/onboarding/generate-questions/"


def test_generate_questions(api_client, auth_headers, mocker):
    mock_response = GenerateQuestionsModelResponseSchema.model_validate(
        {
            "questions": [
                {
                    "key": "services",
                    "question": "What services do you offer and what are their prices?",
                    "reason": "Needed for accurate service and pricing responses.",
                    "required": True,
                },
                {
                    "key": "working_hours",
                    "question": "What are your business working hours by day?",
                    "reason": "Required for availability and booking guidance.",
                    "required": True,
                },
            ]
        }
    )
    mocker.patch(
        "apps.agent.services.openai_client.OpenAIClientService.generate_structured_response",
        return_value=mock_response,
    )
    payload = {
        "business_id": "business_123",
        "business_type": "clinic",
        "onboarding_data": {"business_name": "Example Clinic"},
        "max_questions": 5,
        "target_language": "en",
    }
    response = api_client.post(URL, json=payload, headers=auth_headers)
    body = response.json()
    assert response.status_code == 200
    assert body["business_id"] == "business_123"
    assert len(body["questions"]) == 2
