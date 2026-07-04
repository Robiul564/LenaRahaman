"""Validation helpers for AI-requested backend actions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from apps.agent.schemas import SUPPORTED_ACTION_TYPES


@dataclass
class ActionValidationResult:
    valid_actions: list[dict[str, Any]]
    unsupported_actions: list[str]


class ActionValidatorService:
    """Ensures requested actions are known and allowed for the tenant."""

    def validate(
        self,
        actions: list[dict[str, Any]],
        available_actions: list[str],
    ) -> ActionValidationResult:
        available_set = set(available_actions)
        globally_supported = set(SUPPORTED_ACTION_TYPES)
        valid_actions: list[dict[str, Any]] = []
        unsupported_actions: list[str] = []

        for action in actions:
            action_type = action.get("type")
            if not action_type:
                unsupported_actions.append("missing_action_type")
                continue

            if action_type not in globally_supported:
                unsupported_actions.append(action_type)
                continue

            if action_type not in available_set:
                unsupported_actions.append(action_type)
                continue

            valid_actions.append(action)

        return ActionValidationResult(
            valid_actions=valid_actions,
            unsupported_actions=sorted(set(unsupported_actions)),
        )
