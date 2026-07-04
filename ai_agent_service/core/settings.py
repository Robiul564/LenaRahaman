from __future__ import annotations

import logging
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "ai-agent-service"
    log_level: str = "INFO"

    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    openai_timeout_seconds: float = 20.0
    openai_max_retries: int = 2

    ai_service_api_key: str = Field(default="", alias="AI_SERVICE_API_KEY")

    agent_rate_limit: str = "120/min"
    onboarding_rate_limit: str = "30/min"
    configuration_rate_limit: str = "30/min"

    redis_url: str = ""

    @property
    def rate_limits(self) -> dict[str, str]:
        return {
            "agent_process": self.agent_rate_limit,
            "onboarding_questions": self.onboarding_rate_limit,
            "onboarding_configuration": self.configuration_rate_limit,
        }


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    configure_logging(settings.log_level)
    return settings
