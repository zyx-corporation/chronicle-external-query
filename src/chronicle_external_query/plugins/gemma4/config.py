from __future__ import annotations

import os
from dataclasses import dataclass

from chronicle_external_query.plugins.contracts import ProviderConfigurationField, ProviderPluginError


GEMMA4_BASE_URL_ENV_VAR = "GEMMA4_BASE_URL"
GEMMA4_MODEL_ENV_VAR = "GEMMA4_MODEL"
GEMMA4_TIMEOUT_ENV_VAR = "GEMMA4_TIMEOUT"
GEMMA4_ENABLED_ENV_VAR = "GEMMA4_ENABLED"
GEMMA4_API_KEY_ENV_VAR = "GEMMA4_API_KEY"


@dataclass(frozen=True)
class Gemma4Config:
    base_url: str
    model: str
    timeout_seconds: float
    enabled: bool
    api_key: str | None = None


def describe_configuration_fields() -> tuple[ProviderConfigurationField, ...]:
    return (
        ProviderConfigurationField(
            key="enabled",
            env_var=GEMMA4_ENABLED_ENV_VAR,
            required=True,
            secret=False,
            description="Explicitly enables the local gemma4 answer plugin when set to true.",
        ),
        ProviderConfigurationField(
            key="base_url",
            env_var=GEMMA4_BASE_URL_ENV_VAR,
            required=True,
            secret=False,
            description="Base URL for the local OpenAI-compatible gemma4 runtime.",
        ),
        ProviderConfigurationField(
            key="model",
            env_var=GEMMA4_MODEL_ENV_VAR,
            required=True,
            secret=False,
            description="Model identifier exposed by the local gemma4 runtime.",
        ),
        ProviderConfigurationField(
            key="timeout",
            env_var=GEMMA4_TIMEOUT_ENV_VAR,
            required=False,
            secret=False,
            description="Optional request timeout in seconds for local gemma4 calls.",
        ),
        ProviderConfigurationField(
            key="api_key",
            env_var=GEMMA4_API_KEY_ENV_VAR,
            required=False,
            secret=True,
            description="Optional API key for local runtimes that still expect authorization headers.",
        ),
    )


def load_config_from_env() -> Gemma4Config:
    enabled = _parse_bool(os.getenv(GEMMA4_ENABLED_ENV_VAR, ""))
    base_url = os.getenv(GEMMA4_BASE_URL_ENV_VAR, "").strip().rstrip("/")
    model = os.getenv(GEMMA4_MODEL_ENV_VAR, "").strip()
    timeout_raw = os.getenv(GEMMA4_TIMEOUT_ENV_VAR, "").strip()
    api_key = os.getenv(GEMMA4_API_KEY_ENV_VAR, "").strip() or None

    timeout_seconds = 30.0
    if timeout_raw:
        try:
            timeout_seconds = float(timeout_raw)
        except ValueError as exc:
            raise ProviderPluginError(
                f"{GEMMA4_TIMEOUT_ENV_VAR} must decode to a number of seconds"
            ) from exc
        if timeout_seconds <= 0:
            raise ProviderPluginError(
                f"{GEMMA4_TIMEOUT_ENV_VAR} must be greater than zero"
            )

    return Gemma4Config(
        base_url=base_url,
        model=model,
        timeout_seconds=timeout_seconds,
        enabled=enabled,
        api_key=api_key,
    )


def availability_reason(config: Gemma4Config) -> str:
    if not config.enabled:
        return f"{GEMMA4_ENABLED_ENV_VAR} is not enabled"
    if not config.base_url:
        return f"missing required env var: {GEMMA4_BASE_URL_ENV_VAR}"
    if not config.model:
        return f"missing required env var: {GEMMA4_MODEL_ENV_VAR}"
    return "configured"


def is_available(config: Gemma4Config) -> bool:
    return availability_reason(config) == "configured"


def _parse_bool(raw: str) -> bool:
    return raw.strip().lower() in {"1", "true", "yes", "on"}
