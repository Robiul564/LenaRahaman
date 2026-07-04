"""Structured logging helpers with privacy masking."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

PHONE_KEYS = {"phone", "phone_number", "mobile", "customer_phone"}
PHONE_PATTERN = re.compile(r"\+?\d{8,15}")


def mask_phone_number(value: str | None) -> str | None:
    if not value:
        return value
    digits = re.sub(r"\D", "", value)
    if len(digits) < 6:
        return "***"
    return f"{digits[:3]}***{digits[-2:]}"


def sanitize_for_logging(payload: Any) -> Any:
    """Recursively masks phone-like values from logs."""
    if isinstance(payload, dict):
        sanitized: dict[str, Any] = {}
        for key, value in payload.items():
            if key.lower() in PHONE_KEYS and isinstance(value, str):
                sanitized[key] = mask_phone_number(value)
            else:
                sanitized[key] = sanitize_for_logging(value)
        return sanitized
    if isinstance(payload, list):
        return [sanitize_for_logging(item) for item in payload]
    if isinstance(payload, str) and PHONE_PATTERN.search(payload):
        return PHONE_PATTERN.sub("***masked-phone***", payload)
    return payload


def log_event(logger: logging.Logger, event: str, **fields: Any) -> None:
    record = {"event": event, **sanitize_for_logging(fields)}
    logger.info(json.dumps(record, ensure_ascii=True))


def build_logging_config(level: str) -> dict[str, Any]:
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "plain": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "plain",
            }
        },
        "root": {"handlers": ["console"], "level": level},
    }
