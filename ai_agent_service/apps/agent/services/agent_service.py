"""Main orchestration service for processing customer messages."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import date, datetime, time
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from apps.agent.schemas import AgentModelResponseSchema
from apps.agent.serializers import ProcessMessageResponseSerializer
from apps.agent.services.action_validator import ActionValidatorService
from apps.agent.services.openai_client import OpenAIClientService
from apps.agent.services.prompt_builder import AgentPromptBuilderService
from apps.common.logging import log_event

logger = logging.getLogger(__name__)

EMERGENCY_KEYWORDS = [
    "emergency",
    "urgent",
    "ambulance",
    "severe pain",
    "chest pain",
    "can't breathe",
    "cant breathe",
    "bleeding",
    "suicide",
]


class AgentService:
    """Handles validation, prompting, model call, and response normalization."""

    def __init__(
        self,
        *,
        prompt_builder: AgentPromptBuilderService | None = None,
        openai_client: OpenAIClientService | None = None,
        action_validator: ActionValidatorService | None = None,
    ) -> None:
        self.prompt_builder = prompt_builder or AgentPromptBuilderService()
        self.openai_client = openai_client or OpenAIClientService()
        self.action_validator = action_validator or ActionValidatorService()

    def process_message(self, payload: dict[str, Any], request_id: str) -> dict[str, Any]:
        business_id = payload["business_id"]
        business_context = payload["business_context"]
        available_actions = payload["available_actions"]

        prompt = self.prompt_builder.build_system_prompt(
            business_context=business_context,
            available_actions=available_actions,
        )
        messages = self._build_messages(prompt, payload)

        log_event(
            logger,
            "agent_process_message_started",
            request_id=request_id,
            business_id=business_id,
            channel=payload.get("channel"),
            customer_phone=payload.get("customer", {}).get("phone"),
        )

        model_output = self.openai_client.generate_structured_response(
            messages=messages,
            schema_model=AgentModelResponseSchema,
            schema_name="agent_process_message_response",
        )
        result = model_output.model_dump()
        result = self._apply_language_fallback(result=result, payload=payload)
        result = self._apply_emergency_override(result=result, payload=payload)
        result = self._enforce_action_availability(
            result=result, available_actions=available_actions
        )
        result = self._normalize_action_ids(result=result)
        result = self._enforce_action_payload_integrity(result=result, payload=payload)
        result = self._clamp_booking_actions_to_working_hours(result=result, payload=payload)

        final_response = {
            "request_id": request_id,
            "business_id": business_id,
            "reply_message": result["reply_message"],
            "reply_language": result["reply_language"],
            "intent": result["intent"],
            "conversation_state": result["conversation_state"],
            "extracted_data": result["extracted_data"],
            "actions": result["actions"],
            "handoff": result["handoff"],
            "safety": result["safety"],
            "internal_summary": result["internal_summary"],
        }
        validated = ProcessMessageResponseSerializer.model_validate(final_response)

        log_event(
            logger,
            "agent_process_message_completed",
            request_id=request_id,
            business_id=business_id,
            intent=final_response["intent"]["name"],
            handoff_required=final_response["handoff"]["required"],
            action_count=len(final_response["actions"]),
        )

        return validated.model_dump(mode="json")

    def _build_messages(self, system_prompt: str, payload: dict[str, Any]) -> list[dict[str, str]]:
        role_map = {"customer": "user", "assistant": "assistant", "system": "system"}
        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

        for item in payload.get("conversation_history", []):
            mapped_role = role_map.get(item["role"], "user")
            messages.append({"role": mapped_role, "content": item["content"]})

        if payload.get("backend_action_results"):
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "Recent backend action results (source of truth for external actions): "
                        + json.dumps(
                            payload["backend_action_results"], ensure_ascii=True, default=str
                        )
                    ),
                }
            )

        latest_payload = {
            "channel": payload.get("channel"),
            "customer": payload.get("customer"),
            "message": payload.get("message"),
        }
        messages.append(
            {
                "role": "user",
                "content": json.dumps(
                    latest_payload,
                    ensure_ascii=True,
                    separators=(",", ":"),
                    default=str,
                ),
            }
        )
        return messages

    def _apply_language_fallback(
        self, result: dict[str, Any], payload: dict[str, Any]
    ) -> dict[str, Any]:
        context = payload["business_context"]
        customer_lang = payload.get("customer", {}).get("language")
        supported_languages = context.get("supported_languages") or []
        default_language = context.get("default_language") or "en"

        selected_language = (
            customer_lang if customer_lang in supported_languages else default_language
        )
        if supported_languages and result["reply_language"] not in supported_languages:
            result["reply_language"] = selected_language
        if not supported_languages and not result.get("reply_language"):
            result["reply_language"] = selected_language
        return result

    def _apply_emergency_override(
        self, result: dict[str, Any], payload: dict[str, Any]
    ) -> dict[str, Any]:
        message_text = (payload.get("message", {}).get("text") or "").lower()
        if not any(keyword in message_text for keyword in EMERGENCY_KEYWORDS):
            return result

        available_actions = payload.get("available_actions", [])
        actions: list[dict[str, Any]] = []
        if "handoff_to_human" in available_actions:
            actions.append(
                {
                    "action_id": str(uuid.uuid4()),
                    "type": "handoff_to_human",
                    "priority": "urgent",
                    "data": {
                        "department": "emergency",
                        "reason": "Potential emergency detected from customer message.",
                    },
                    "requires_backend_result": False,
                }
            )

        result["intent"] = {"name": "human_handoff", "confidence": 0.99}
        result["conversation_state"] = {
            "status": "escalated",
            "current_flow": "emergency_handoff",
            "next_required_information": [],
        }
        result["handoff"] = {
            "required": True,
            "department": "emergency",
            "priority": "urgent",
            "reason": "Potential emergency or high-risk request detected.",
        }
        result["safety"] = {
            "flagged": True,
            "category": "high_risk_or_emergency",
            "instructions": (
                "Do not provide regulated emergency advice. "
                "Ask the customer to contact local emergency services."
            ),
        }
        result["reply_message"] = (
            "This sounds urgent. Please contact local emergency services immediately. "
            "I am connecting you with a human support teammate now."
        )
        result["actions"] = actions
        result["internal_summary"] = (
            "Emergency keyword detected; urgent handoff triggered and safety instructions applied."
        )
        return result

    def _enforce_action_availability(
        self,
        *,
        result: dict[str, Any],
        available_actions: list[str],
    ) -> dict[str, Any]:
        validation = self.action_validator.validate(result.get("actions", []), available_actions)
        result["actions"] = validation.valid_actions

        if not validation.unsupported_actions:
            return result

        unsupported_types = ", ".join(validation.unsupported_actions)
        if "handoff_to_human" in available_actions:
            result["handoff"] = {
                "required": True,
                "department": "support",
                "priority": "normal",
                "reason": f"Unavailable required action(s): {unsupported_types}.",
            }
            result["actions"].append(
                {
                    "action_id": str(uuid.uuid4()),
                    "type": "handoff_to_human",
                    "priority": "normal",
                    "data": {"reason": f"Unsupported actions requested: {unsupported_types}"},
                    "requires_backend_result": False,
                }
            )
            result["reply_message"] = (
                "I need help from a human teammate to continue this request. "
                "I am routing this conversation now."
            )
        else:
            result["reply_message"] = (
                "I cannot complete that request with current available actions. "
                "Could you choose an alternative option?"
            )
            result["handoff"] = {
                "required": False,
                "department": None,
                "priority": None,
                "reason": f"Unsupported actions requested: {unsupported_types}.",
            }

        existing_summary = result.get("internal_summary", "")
        result["internal_summary"] = (
            f"{existing_summary} Unsupported actions filtered: {unsupported_types}."
        ).strip()
        return result

    def _normalize_action_ids(self, *, result: dict[str, Any]) -> dict[str, Any]:
        for action in result.get("actions", []):
            action_id = action.get("action_id")
            if not self._is_valid_uuid(action_id):
                action["action_id"] = str(uuid.uuid4())
        return result

    def _enforce_action_payload_integrity(
        self,
        *,
        result: dict[str, Any],
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        valid_service_ids = {
            service.get("service_id")
            for service in payload.get("business_context", {}).get("services", [])
            if service.get("service_id")
        }

        invalid_reasons: list[str] = []
        valid_actions: list[dict[str, Any]] = []

        for action in result.get("actions", []):
            action_type = action.get("type")
            action_data = action.get("data")

            if not isinstance(action_data, dict):
                invalid_reasons.append(f"{action_type}:data_must_be_object")
                continue

            if action_type == "check_availability":
                service_id = action_data.get("service_id")
                requested_date = action_data.get("requested_date") or action_data.get("date")

                if not service_id:
                    invalid_reasons.append("check_availability:missing_service_id")
                    continue
                if valid_service_ids and service_id not in valid_service_ids:
                    invalid_reasons.append("check_availability:unknown_service_id")
                    continue
                if not requested_date:
                    invalid_reasons.append("check_availability:missing_requested_date")
                    continue

            if action_type in {"create_booking", "reschedule_booking"}:
                service_id = action_data.get("service_id")
                if service_id and valid_service_ids and service_id not in valid_service_ids:
                    invalid_reasons.append(f"{action_type}:unknown_service_id")
                    continue

            valid_actions.append(action)

        result["actions"] = valid_actions

        if not invalid_reasons:
            return result

        existing_summary = result.get("internal_summary", "")
        result["internal_summary"] = (
            f"{existing_summary} Invalid action payloads filtered: {', '.join(invalid_reasons)}."
        ).strip()

        missing_date = any(reason.endswith("missing_requested_date") for reason in invalid_reasons)
        missing_service = any("service_id" in reason for reason in invalid_reasons)
        if missing_date or missing_service:
            next_info = result.setdefault("conversation_state", {}).setdefault(
                "next_required_information", []
            )
            if missing_service and "service_interest" not in next_info:
                next_info.append("service_interest")
            if missing_date and "preferred_date" not in next_info:
                next_info.append("preferred_date")

        return result

    def _clamp_booking_actions_to_working_hours(
        self,
        *,
        result: dict[str, Any],
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        context = payload.get("business_context", {})
        timezone_name = context.get("timezone") or "UTC"
        working_hours = context.get("working_hours") or []

        working_map: dict[str, tuple[time, time]] = {}
        for entry in working_hours:
            day = entry.get("day")
            open_time = self._parse_hhmm(entry.get("open"))
            close_time = self._parse_hhmm(entry.get("close"))
            if day and open_time and close_time and open_time < close_time:
                working_map[day] = (open_time, close_time)

        if not working_map:
            return result

        adjusted_window = False
        unavailable_days = False
        kept_actions: list[dict[str, Any]] = []

        for action in result.get("actions", []):
            action_type = action.get("type")
            if action_type not in {"check_availability", "create_booking", "reschedule_booking"}:
                kept_actions.append(action)
                continue

            data = action.get("data") or {}
            requested_date = (
                data.get("requested_date")
                or data.get("date")
                or data.get("preferred_date")
                or data.get("appointment_date")
            )
            if not requested_date:
                kept_actions.append(action)
                continue

            day_name = self._day_name_for_date(requested_date, timezone_name)
            if not day_name or day_name not in working_map:
                if action_type == "check_availability":
                    unavailable_days = True
                    continue
                kept_actions.append(action)
                continue

            open_time, close_time = working_map[day_name]

            if "time_range_start" in data or "time_range_end" in data:
                start = self._parse_hhmm(data.get("time_range_start")) or open_time
                end = self._parse_hhmm(data.get("time_range_end")) or close_time

                clamped_start = max(start, open_time)
                clamped_end = min(end, close_time)

                if clamped_start >= clamped_end:
                    clamped_start, clamped_end = open_time, close_time

                if clamped_start != start or clamped_end != end:
                    adjusted_window = True

                data["time_range_start"] = self._format_hhmm(clamped_start)
                data["time_range_end"] = self._format_hhmm(clamped_end)

            for point_key in ("requested_time", "time", "preferred_time"):
                raw_point = data.get(point_key)
                if not raw_point:
                    continue

                parsed_point = self._parse_hhmm(raw_point)
                if parsed_point is None:
                    data[point_key] = None
                    adjusted_window = True
                    self._append_next_info(result, "preferred_time")
                    continue

                if not (open_time <= parsed_point < close_time):
                    data[point_key] = None
                    adjusted_window = True
                    self._append_next_info(result, "preferred_time")

            action["data"] = data
            kept_actions.append(action)

        result["actions"] = kept_actions

        if unavailable_days:
            result["reply_message"] = (
                "We are closed on that day. "
                "Please share another preferred date within business hours."
            )
            self._append_next_info(result, "preferred_date")
            self._append_internal_summary(
                result,
                "Removed booking availability action for non-working day.",
            )

        if adjusted_window:
            self._append_internal_summary(
                result,
                "Adjusted requested booking time window to business working hours.",
            )

        return result

    @staticmethod
    def _is_valid_uuid(value: Any) -> bool:
        if not value:
            return False
        try:
            uuid.UUID(str(value))
            return True
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _parse_hhmm(raw_value: Any) -> time | None:
        if not isinstance(raw_value, str):
            return None
        try:
            return datetime.strptime(raw_value, "%H:%M").time()
        except ValueError:
            return None

    @staticmethod
    def _format_hhmm(value: time) -> str:
        return value.strftime("%H:%M")

    @staticmethod
    def _day_name_for_date(date_text: str, timezone_name: str) -> str | None:
        try:
            requested = date.fromisoformat(str(date_text))
        except ValueError:
            return None

        try:
            ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError:
            pass

        return requested.strftime("%A").lower()

    @staticmethod
    def _append_next_info(result: dict[str, Any], info_key: str) -> None:
        conversation_state = result.setdefault("conversation_state", {})
        next_required = conversation_state.setdefault("next_required_information", [])
        if info_key not in next_required:
            next_required.append(info_key)

    @staticmethod
    def _append_internal_summary(result: dict[str, Any], addition: str) -> None:
        existing_summary = result.get("internal_summary", "")
        if not existing_summary:
            result["internal_summary"] = addition
            return
        if addition not in existing_summary:
            result["internal_summary"] = f"{existing_summary} {addition}"
