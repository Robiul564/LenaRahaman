# Backend Developer Handoff

## 1) How to Call the AI Service

- Endpoint: `POST /api/v1/agent/process-message/`
- Header: `X-AI-Service-Key: <AI_SERVICE_API_KEY>`
- Content type: `application/json`
- Include `business_id` in every call.

## 2) Required Request Fields

Required top-level keys:

- `business_id`
- `channel`
- `customer`
- `message`
- `business_context`
- `available_actions`

Optional:

- `conversation_history`
- `backend_action_results`

## 3) How to Send Conversation History

- Send historical turns in `conversation_history`.
- Use role mapping:
  - customer -> `"role": "customer"`
  - ai previous message -> `"role": "assistant"`
- Keep in chronological order.
- Include the latest incoming message under `message`.

## 4) How to Send Business Configuration

- Send all AI-relevant business settings in `business_context` on every request.
- Include services, pricing, policies, handoff rules, lead fields, and available staff.
- The AI service does not fetch config from any database.

## 5) How to Execute Returned Actions

- Read `actions[]` from response.
- Execute each action using your own backend integrations (calendar, CRM, payment, etc.).
- Treat action `data` as intent parameters, not final truth.
- For `requires_backend_result=true`, send execution result in next call.

Reliability guarantees from AI service:

- Every returned `action_id` is normalized to UUID format.
- Unknown or invalid action payloads are filtered before response.
- `check_availability` actions are validated against known service IDs.
- Availability/booking windows are clamped to tenant `working_hours`.
- If requested date is a non-working day, availability action is removed and `preferred_date` is requested.

## 6) How to Send Backend Action Results Back

Use `backend_action_results` in the next `process-message` request:

```json
{
  "backend_action_results": [
    {
      "action_id": "uuid",
      "type": "check_availability",
      "success": true,
      "data": {
        "available_slots": [
          {
            "start": "2026-07-03T10:00:00+06:00",
            "end": "2026-07-03T10:30:00+06:00"
          }
        ]
      },
      "error": null
    }
  ]
}
```

## 7) How to Store Agent Configuration

- Use `/api/v1/onboarding/build-configuration/` output as normalized config.
- Store resulting `agent_configuration` in your backend database.
- Send this configuration (or mapped equivalent) in `business_context` during processing calls.

## 8) Idempotency Handling

- Create backend idempotency key per inbound customer message.
- Recommended key: `business_id + customer_id + message_id`.
- Ensure external action execution is deduplicated on retries.

## 9) Human Handoff Handling

- If response has `handoff.required=true`, escalate according to `department` and `priority`.
- If action includes `handoff_to_human`, create support case/owner alert internally.
- Preserve `reason` for agent audit and operator context.

## 10) Error and Retry Handling

- Retry with backoff for:
  - `RATE_LIMITED` (429)
  - `OPENAI_API_ERROR` (502)
- Do not retry unchanged requests for:
  - `AUTHENTICATION_FAILED` (401)
  - `VALIDATION_ERROR` (400)
- Log and alert for repeated `INTERNAL_SERVER_ERROR`.

## 11) Prevent Cross-Business Data Leakage

- Never reuse `business_context` across tenants.
- Always verify `business_id` before sending request payload.
- Keep tenant-specific action execution paths isolated.
- Never combine conversation history from different businesses/customers.
