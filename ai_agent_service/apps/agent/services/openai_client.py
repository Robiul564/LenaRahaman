"""OpenAI integration service for structured JSON outputs."""

from __future__ import annotations

import json
from typing import Any

from openai import APIConnectionError, APIError, APITimeoutError, OpenAI, RateLimitError
from pydantic import BaseModel, ValidationError

from apps.common.exceptions import OpenAIInvalidResponseError, OpenAIServiceError
from core.settings import get_settings


class OpenAIClientService:
    """Wraps OpenAI SDK calls with retries and schema validation."""

    def __init__(self, client: OpenAI | None = None) -> None:
        settings = get_settings()
        self.api_key = settings.openai_api_key
        self.model = settings.openai_model
        self.timeout_seconds = settings.openai_timeout_seconds
        self.max_retries = settings.openai_max_retries
        self.client = client or OpenAI(api_key=self.api_key, timeout=self.timeout_seconds)

    def _extract_response_text(self, response: Any) -> str:
        output_text = getattr(response, "output_text", None)
        if isinstance(output_text, str) and output_text.strip():
            return output_text

        output = getattr(response, "output", None)
        if isinstance(output, list):
            for item in output:
                content = getattr(item, "content", None)
                if isinstance(content, list):
                    for chunk in content:
                        text = getattr(chunk, "text", None)
                        if isinstance(text, str) and text.strip():
                            return text
        raise OpenAIInvalidResponseError("OpenAI response did not contain readable text output.")

    @staticmethod
    def _api_error_details(exc: Exception) -> list[dict[str, Any]]:
        details: list[dict[str, Any]] = []
        status_code = getattr(exc, "status_code", None)
        if status_code is not None:
            details.append({"status_code": status_code})

        body = getattr(exc, "body", None)
        if body is not None:
            details.append({"provider_body": body})
        else:
            details.append({"provider_error": str(exc)})

        return details

    def generate_structured_response(
        self,
        *,
        messages: list[dict[str, Any]],
        schema_model: type[BaseModel],
        schema_name: str,
    ) -> BaseModel:
        if not self.api_key:
            raise OpenAIServiceError("OPENAI_API_KEY is missing.")

        schema = schema_model.model_json_schema(mode="validation")

        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.responses.create(
                    model=self.model,
                    input=messages,
                    temperature=0,
                    text={
                        "format": {
                            "type": "json_schema",
                            "name": schema_name,
                            # Non-strict mode keeps structured outputs while allowing
                            # free-form objects such as action.data payloads.
                            "strict": False,
                            "schema": schema,
                        }
                    },
                )
                raw_text = self._extract_response_text(response)
                payload = json.loads(raw_text)
                return schema_model.model_validate(payload)
            except (APITimeoutError, APIConnectionError, RateLimitError) as exc:
                last_error = exc
                if attempt < self.max_retries:
                    continue
                raise OpenAIServiceError(
                    "OpenAI API temporary failure after retries.",
                    details=self._api_error_details(exc),
                ) from exc
            except APIError as exc:
                raise OpenAIServiceError(
                    "OpenAI API request failed.",
                    details=self._api_error_details(exc),
                ) from exc
            except (ValidationError, json.JSONDecodeError, TypeError, ValueError) as exc:
                raise OpenAIInvalidResponseError("Structured output validation failed.") from exc

        raise OpenAIServiceError("OpenAI API failed unexpectedly.") from last_error
