# AI Agent Service (`ai_agent_service`)

Standalone, stateless **FastAPI** service for multi-tenant AI agent reasoning.

This service receives customer messages and business context from a main backend, calls OpenAI with structured output, validates the result, and returns safe action plans and reply content. It does not connect directly to WhatsApp, Meta, CRM, calendar, payment, or your main SaaS database.

## Requirements

- Python 3.12+
- OpenAI API key
- Redis (optional, currently in-memory throttling is used)

## Installation

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8000
```

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn main:app --reload --port 8000
```

## Endpoints

- `GET /api/v1/health/`
- `POST /api/v1/agent/process-message/`
- `POST /api/v1/onboarding/generate-questions/`
- `POST /api/v1/onboarding/build-configuration/`

All non-health endpoints require:

```text
X-AI-Service-Key: <AI_SERVICE_API_KEY>
```

## Production Reliability Safeguards

- Action IDs are normalized to UUIDs before responses are returned.
- Unsupported or invalid action payloads are filtered server-side.
- `check_availability` requests are validated against known service IDs.
- Booking/availability time windows are clamped to business working hours.
- If requested date falls on a non-working day, booking availability action is removed and the response asks for a new date.
- OpenAI provider errors are returned with diagnostic details in `error.details`.

## API Docs

- Swagger UI: `GET /docs`
- OpenAPI JSON: `GET /openapi.json`

## Testing

```bash
pytest
```

## Docker

```bash
cp .env.example .env
docker compose up --build
```
