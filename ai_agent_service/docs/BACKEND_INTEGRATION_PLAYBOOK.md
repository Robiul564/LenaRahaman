# Backend Integration Playbook (All Scenarios)

This guide is for the main backend developer integrating with the AI Agent Service.

## 1) System Boundary (Who Does What)

- Main backend owns business onboarding, authentication, WhatsApp webhooks, customer profiles, chat history, booking DB, CRM, payments, tickets, and message delivery.
- AI Agent Service is stateless and only returns structured decision JSON.
- AI Agent Service does not send WhatsApp messages directly.
- AI Agent Service does not persist tenant/customer data.

## 2) Required API Contract

- Base endpoint: `POST /api/v1/agent/process-message/`
- Header: `X-AI-Service-Key: <AI_SERVICE_API_KEY>`
- Content-Type: `application/json`
- Must include `business_id` in every request.
- Must include full per-tenant `business_context` in every request.
- Must include allowed `available_actions` for this exact request.

## 3) Core Processing Loop

1. Receive customer message from WhatsApp webhook.
2. Resolve tenant and customer.
3. Build `process-message` payload with current context/history.
4. Call AI service.
5. Parse AI response.
6. Execute returned `actions` in backend systems.
7. If action result is needed, call AI again with `backend_action_results`.
8. Send final `reply_message` through WhatsApp provider.
9. Store both request/response and execution logs in backend DB.

## 4) Multi-Tenant Safety Rules

- Always resolve tenant before building payload.
- Never reuse `business_context` from another tenant.
- Never mix conversation history across customers.
- Enforce tenant-scoped IDs in all action execution.
- Keep idempotency key tenant-scoped.

Recommended idempotency key:

- `business_id + customer_id + message_id`

## 5) Action Execution Rules

- Treat `actions[]` as backend tasks, not final outcomes.
- Execute only actions listed in response.
- Store action status (`queued`, `success`, `failed`) with `action_id`.
- For `requires_backend_result=true`, call AI again including result object.
- Never confirm booking/payment/refund/order before backend success.

## 6) Reliability Guards Already Enforced by AI Service

- Action IDs are normalized to UUID format.
- Unsupported actions are filtered.
- Invalid action payloads are filtered.
- `check_availability` validates service IDs.
- Booking windows are clamped to business working hours.
- Non-working-day availability actions are removed and date is requested again.
- Emergency-like messages trigger safety escalation behavior.

## 7) Scenario Playbook

### Scenario A: Greeting / FAQ

- Call AI with current message and context.
- If no action returned, send `reply_message` directly.
- Persist intent and response in backend analytics.

### Scenario B: Booking Request (New)

- AI usually returns `check_availability` action.
- Backend checks calendar/staff rules.
- Backend sends `backend_action_results` with available slots.
- AI returns customer-friendly slot question.

### Scenario C: Availability Follow-up

- Customer selects a slot.
- AI may return `create_booking` action.
- Backend creates booking.
- Backend returns booking success/failure to AI.
- AI returns final confirmation/fallback message.

### Scenario D: Cancellation / Reschedule

- AI returns `cancel_booking` or `reschedule_booking`.
- Backend verifies booking ownership and policy.
- Backend returns result.
- AI generates customer update.

### Scenario E: Lead Capture / Qualification

- AI extracts lead fields and may return `create_lead`/`update_lead`.
- Backend writes to CRM.
- Backend optionally returns write result.
- AI asks only missing required fields next.

### Scenario F: Complaint / Human Request

- AI sets `handoff.required=true` and/or action `handoff_to_human`.
- Backend creates support case and routes to queue.
- Backend sends acknowledgment to customer.

### Scenario G: Emergency / High Risk

- AI marks `safety.flagged=true` and urgent handoff.
- Backend must immediately escalate to human queue.
- Backend should avoid automated medical/legal advice responses.

### Scenario H: Payment Link Request

- AI may return `request_payment_link` action.
- Backend generates secure payment URL.
- Backend sends action result back to AI.
- AI sends customer-facing payment guidance.

### Scenario I: Order Tracking

- AI returns `track_order` action if available.
- Backend fetches tracking status.
- Backend sends result back.
- AI returns concise status message.

### Scenario J: Unsupported Action Requested by Model

- AI service filters unsupported action.
- Response may suggest handoff/fallback question.
- Backend follows returned handoff/fallback response.

## 8) Error Handling and Retry Policy

- `401 AUTHENTICATION_FAILED`: do not retry until key fixed.
- `400 VALIDATION_ERROR`: do not retry; fix payload contract.
- `429 RATE_LIMITED`: retry with exponential backoff + jitter.
- `502 OPENAI_API_ERROR`: retry with bounded attempts.
- `502 OPENAI_INVALID_RESPONSE`: retry once, then fallback to human handoff.
- `500 INTERNAL_SERVER_ERROR`: retry with backoff and alert.

Recommended retry strategy:

- Maximum 3 attempts.
- Backoff: 1s, 2s, 4s (+ jitter).

## 9) Observability and Audit

Store in backend logs/DB for each turn:

- `request_id` from AI response headers/body.
- `business_id`, `customer_id`, `message_id`.
- AI intent, handoff flag, safety flag.
- Returned actions and execution outcomes.
- Final outbound WhatsApp message ID.

## 10) Security Checklist

- Keep `AI_SERVICE_API_KEY` in secret manager.
- Restrict AI service network access to backend only.
- Do not log raw API keys.
- Mask phone numbers in backend logs.
- Sign/verify internal service-to-service calls if possible.

## 11) Deployment Recommendations

- Run multiple AI service instances behind load balancer.
- Use Redis for distributed rate limiting.
- Apply request timeout on backend calls to AI (10-20s).
- Add circuit breaker in backend for repeated 5xx.
- Add fallback path: human handoff when AI unavailable.

## 12) Minimal Backend Pseudocode

```python
payload = build_ai_payload(incoming_message, tenant, customer, history)
resp = ai_client.process_message(payload)

for action in resp.actions:
    result = execute_action(action, tenant_context)
    if action.requires_backend_result:
        payload2 = build_followup_payload(
            incoming_message=incoming_message,
            tenant=tenant,
            customer=customer,
            history=history_plus(resp.reply_message),
            backend_action_results=[result],
        )
        resp = ai_client.process_message(payload2)

send_whatsapp(resp.reply_message)
store_turn_audit(resp, payload)
```

## 13) Pre-Go-Live UAT Checklist

- Booking happy path from first message to confirmed booking.
- Non-working-day booking attempt.
- Missing field collection flow.
- Complaint and explicit human handoff.
- Emergency escalation behavior.
- OpenAI temporary failure retry behavior.
- Tenant isolation under concurrent traffic.
- Idempotency on duplicate webhook delivery.

## 14) Existing Reference Docs

- `docs/API_INTEGRATION.md`
- `docs/BACKEND_DEVELOPER_HANDOFF.md`
- `docs/EXAMPLE_REQUESTS.md`
- `docs/AI_AGENT_ARCHITECTURE.md`
