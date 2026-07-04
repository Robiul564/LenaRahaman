# API Integration Guide

## Base URL

`https://<ai-agent-service-host>`

## Authentication

All non-health endpoints require:

```text
X-AI-Service-Key: <AI_SERVICE_API_KEY>
Content-Type: application/json
```

If missing/invalid, service returns `401 AUTHENTICATION_FAILED`.

## Endpoints

1. `GET /api/v1/health/`
2. `POST /api/v1/agent/process-message/`
3. `POST /api/v1/onboarding/generate-questions/`
4. `POST /api/v1/onboarding/build-configuration/`

## `POST /api/v1/agent/process-message/`

Main backend sends full message context and available actions.

### Request (example)

```json
{
  "business_id": "business_123",
  "channel": "whatsapp",
  "customer": {
    "customer_id": "customer_456",
    "name": "John Doe",
    "phone": "+8801712345678",
    "language": "en"
  },
  "message": {
    "message_id": "message_789",
    "text": "I want to book an appointment tomorrow.",
    "message_type": "text",
    "timestamp": "2026-07-02T10:00:00Z"
  },
  "business_context": {
    "business_name": "Example Clinic",
    "business_type": "clinic",
    "supported_languages": ["en", "bn"],
    "default_language": "en",
    "services": [
      {
        "service_id": "service_1",
        "name": "General Consultation",
        "price": 1000,
        "currency": "BDT",
        "duration_minutes": 30,
        "booking_required": true
      }
    ]
  },
  "conversation_history": [],
  "available_actions": [
    "send_message",
    "check_availability",
    "create_booking",
    "handoff_to_human"
  ],
  "backend_action_results": []
}
```

### Response (example)

```json
{
  "request_id": "8ca67d8c-9792-4d72-9165-87f4f71da220",
  "business_id": "business_123",
  "reply_message": "I can help you book an appointment. Which time would you prefer tomorrow?",
  "reply_language": "en",
  "intent": {
    "name": "booking_request",
    "confidence": 0.95
  },
  "conversation_state": {
    "status": "active",
    "current_flow": "booking",
    "next_required_information": ["preferred_time"]
  },
  "extracted_data": {
    "customer": {
      "name": null,
      "phone": null,
      "email": null,
      "language": "en"
    },
    "lead": {
      "service_interest": "General Consultation",
      "budget": null,
      "preferred_date": "2026-07-03",
      "preferred_time": null,
      "notes": "Customer wants an appointment tomorrow."
    }
  },
  "actions": [
    {
      "action_id": "9c3d5d33-fecd-4a0d-a59f-036b40f5a7f0",
      "type": "check_availability",
      "priority": "normal",
      "data": {
        "service_id": "service_1",
        "requested_date": "2026-07-03"
      },
      "requires_backend_result": true
    }
  ],
  "handoff": {
    "required": false,
    "department": null,
    "priority": null,
    "reason": null
  },
  "safety": {
    "flagged": false,
    "category": null,
    "instructions": null
  },
  "internal_summary": "Customer asked for booking and still needs preferred time."
}
```

## `POST /api/v1/onboarding/generate-questions/`

Generates top missing onboarding questions from partial answers.

### Request

```json
{
  "business_id": "business_123",
  "business_type": "clinic",
  "onboarding_data": {
    "business_name": "Example Clinic"
  },
  "max_questions": 8,
  "target_language": "en"
}
```

### Response

```json
{
  "request_id": "2c9241f7-89f3-477d-9a16-dca36f3140b4",
  "business_id": "business_123",
  "questions": [
    {
      "key": "services",
      "question": "What services do you offer and what are their prices?",
      "reason": "Needed for accurate customer replies.",
      "required": true
    }
  ]
}
```

## `POST /api/v1/onboarding/build-configuration/`

Builds normalized agent configuration from completed onboarding answers.

### Request

```json
{
  "business_id": "business_123",
  "business_type": "clinic",
  "onboarding_answers": {
    "business_name": "Example Clinic",
    "supported_languages": ["en", "bn"]
  }
}
```

### Response

```json
{
  "request_id": "8f54f9a9-6709-4a54-8e4e-6e5259adf8ea",
  "business_id": "business_123",
  "agent_configuration": {
    "business_profile": {
      "business_name": "Example Clinic",
      "business_type": "clinic"
    },
    "services": [],
    "staff_members": [],
    "working_hours": [],
    "faqs": [],
    "policies": [],
    "booking_rules": {},
    "lead_qualification": {},
    "handoff_rules": [],
    "supported_languages": ["en", "bn"],
    "default_language": "en",
    "brand_tone": "professional, helpful",
    "restricted_topics": [],
    "available_actions": [],
    "agent_rules": []
  }
}
```

## Error Handling

All errors follow:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request payload.",
    "details": []
  }
}
```

Supported error codes:

- `VALIDATION_ERROR`
- `AUTHENTICATION_FAILED`
- `OPENAI_API_ERROR`
- `OPENAI_INVALID_RESPONSE`
- `UNSUPPORTED_ACTION`
- `RATE_LIMITED`
- `INTERNAL_SERVER_ERROR`

## Retry Rules

- Retry on `429 RATE_LIMITED` with exponential backoff and jitter.
- Retry on `502 OPENAI_API_ERROR` with bounded retries.
- Do not retry `VALIDATION_ERROR` or `AUTHENTICATION_FAILED` until payload/header is fixed.

## Timeout Recommendations

- Main backend request timeout to AI service: `10-20s`.
- AI service OpenAI timeout is env-configurable (`OPENAI_TIMEOUT_SECONDS`, default `20`).
- Use async or queue handoff for long-running workflows.

## Idempotency Guidance

- Main backend should store and reuse its own idempotency keys per inbound message.
- Recommended dedupe key: `business_id + customer_id + message_id`.
- If repeated calls happen, backend should prevent duplicated external actions.
