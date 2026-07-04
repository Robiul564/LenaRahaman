from apps.agent.services.prompt_builder import AgentPromptBuilderService


def test_prompt_builder_includes_business_context_and_actions():
    builder = AgentPromptBuilderService()
    prompt = builder.build_system_prompt(
        business_context={
            "business_name": "Example Clinic",
            "business_type": "clinic",
            "services": [{"service_id": "service_1", "name": "Consultation"}],
            "agent_rules": ["Only use provided business context."],
        },
        available_actions=["check_availability", "create_booking"],
    )

    assert "Example Clinic" in prompt
    assert "check_availability" in prompt
    assert "create_booking" in prompt
    assert "JSON schema" in prompt
    assert "Hello, I need an appointment." not in prompt
