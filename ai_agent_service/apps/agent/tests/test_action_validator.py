from apps.agent.services.action_validator import ActionValidatorService


def test_action_validator_accepts_supported_and_available_actions():
    validator = ActionValidatorService()
    actions = [
        {
            "action_id": "a1",
            "type": "check_availability",
            "priority": "normal",
            "data": {},
            "requires_backend_result": True,
        }
    ]
    result = validator.validate(
        actions=actions, available_actions=["check_availability", "send_message"]
    )
    assert result.unsupported_actions == []
    assert len(result.valid_actions) == 1


def test_action_validator_flags_unavailable_or_unknown_actions():
    validator = ActionValidatorService()
    actions = [
        {"action_id": "a1", "type": "create_booking", "priority": "normal", "data": {}},
        {"action_id": "a2", "type": "unknown_action", "priority": "normal", "data": {}},
    ]
    result = validator.validate(actions=actions, available_actions=["send_message"])
    assert result.valid_actions == []
    assert set(result.unsupported_actions) == {"create_booking", "unknown_action"}
