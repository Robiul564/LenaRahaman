# AI Agent Architecture

## AI Service Role

This service is a stateless AI reasoning layer. It:

- Validates incoming payloads.
- Builds dynamic prompts from tenant business context.
- Processes conversation history and backend action results.
- Returns structured reply/action JSON.
- Generates onboarding questions.
- Normalizes onboarding answers into agent configuration.

It does **not** directly call WhatsApp, Meta APIs, CRM, calendar, or payments.

## Main Backend Role

The main backend:

- Owns user auth and business registration.
- Receives WhatsApp webhooks and maps to `business_id`.
- Stores customer profile, message history, and business configuration.
- Executes external actions requested by AI.
- Sends action results back to AI service.

## Multi-Tenant Data Isolation

- Every request must include `business_id`.
- Service does not persist tenant content in models/tables.
- Business context is request-scoped and provided by the main backend each call.
- Response always echoes the provided `business_id`.

## Message Processing Flow

1. Main backend sends validated request to `/api/v1/agent/process-message/`.
2. API key auth and throttle checks run.
3. DRF serializer validates schema.
4. Prompt builder generates tenant-specific system instructions.
5. Conversation history and latest message are passed separately as OpenAI messages.
6. OpenAI returns strict JSON schema output.
7. Pydantic + DRF validate output again.
8. Action validator filters unsupported/unavailable actions.
9. Service returns normalized response with handoff/safety flags.

## Prompt-Building Flow

- Source inputs:
  - business profile and type
  - services/staff/hours
  - FAQs/policies
  - booking and lead qualification rules
  - handoff rules and agent rules
  - supported languages
  - available actions
- Prompt enforces:
  - no hallucinated business facts
  - no direct booking/payment confirmations without backend results
  - strict JSON schema response only

## Action Request Flow

1. AI returns requested actions.
2. Service validates each action against:
   - globally supported action set
   - request-level `available_actions`
3. Unsupported actions are removed.
4. Service recommends human handoff or fallback response when necessary.
5. Main backend executes remaining actions.

## Backend Result Follow-Up Flow

1. Main backend executes action and gathers result payload.
2. Result is sent back in `backend_action_results` in next process call.
3. AI service uses result context to produce next message and action step.

## Security Rules

- API key auth on all non-health endpoints.
- Scoped throttling per API domain.
- Request ID middleware for tracing.
- Standardized error envelopes.
- Logging masks phone numbers and avoids API key leaks.
- No persistent storage of customer/private payloads.
