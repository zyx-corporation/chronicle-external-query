from __future__ import annotations

import os
from dataclasses import dataclass

from chronicle_external_query.plugins.contracts import ProviderConfigurationField, ProviderPluginError


HOSTED_OPENAI_ENABLED_ENV_VAR = "OPENAI_COMPATIBLE_HOSTED_ENABLED"
HOSTED_OPENAI_BASE_URL_ENV_VAR = "OPENAI_COMPATIBLE_HOSTED_BASE_URL"
HOSTED_OPENAI_MODEL_ENV_VAR = "OPENAI_COMPATIBLE_HOSTED_MODEL"
HOSTED_OPENAI_API_KEY_ENV_VAR = "OPENAI_COMPATIBLE_HOSTED_API_KEY"
HOSTED_OPENAI_TIMEOUT_ENV_VAR = "OPENAI_COMPATIBLE_HOSTED_TIMEOUT"


@dataclass(frozen=True)
class HostedOpenAICompatibleConfig:
    enabled: bool
    base_url: str
    model: str
    api_key: str
    timeout_seconds: float


def describe_configuration_fields() -> tuple[ProviderConfigurationField, ...]:
    return (
        ProviderConfigurationField(
            key="enabled",
            env_var=HOSTED_OPENAI_ENABLED_ENV_VAR,
            required=True,
            secret=False,
            description="Explicitly enables the hosted OpenAI-compatible plugin.",
        ),
        ProviderConfigurationField(
            key="base_url",
            env_var=HOSTED_OPENAI_BASE_URL_ENV_VAR,
            required=True,
            secret=False,
            description="Base URL for the hosted OpenAI-compatible provider.",
        ),
        ProviderConfigurationField(
            key="model",
            env_var=HOSTED_OPENAI_MODEL_ENV_VAR,
            required=True,
            secret=False,
            description="Model identifier for the hosted provider.",
        ),
        ProviderConfigurationField(
            key="api_key",
            env_var=HOSTED_OPENAI_API_KEY_ENV_VAR,
            required=True,
            secret=True,
            description="API key for the hosted provider.",
        ),
        ProviderConfigurationField(
            key="timeout",
            env_var=HOSTED_OPENAI_TIMEOUT_ENV_VAR,
            required=False,
            secret=False,
            description="Optional timeout in seconds for hosted provider requests.",
        ),
    )


def load_config_from_env() -> HostedOpenAICompatibleConfig:
    enabled = _parse_bool(os.getenv(HOSTED_OPENAI_ENABLED_ENV_VAR, ""))
    base_url = os.getenv(HOSTED_OPENAI_BASE_URL_ENV_VAR, "").strip().rstrip("/")
    model = os.getenv(HOSTED_OPENAI_MODEL_ENV_VAR, "").strip()
    api_key = os.getenv(HOSTED_OPENAI_API_KEY_ENV_VAR, "").strip()
    timeout_raw = os.getenv(HOSTED_OPENAI_TIMEOUT_ENV_VAR, "").strip()

    timeout_seconds = 30.0
    if timeout_raw:
        try:
            timeout_seconds = float(timeout_raw)
        except ValueError as exc:
            raise ProviderPluginError(
                f"{HOSTED_OPENAI_TIMEOUT_ENV_VAR} must decode to a number of seconds"
            ) from exc
        if timeout_seconds <= 0:
            raise ProviderPluginError(
                f"{HOSTED_OPENAI_TIMEOUT_ENV_VAR} must be greater than zero"
            )

    return HostedOpenAICompatibleConfig(
        enabled=enabled,
        base_url=base_url,
        model=model,
        api_key=api_key,
        timeout_seconds=timeout_seconds,
    )


def availability_reason(config: HostedOpenAICompatibleConfig) -> str:
    if not config.enabled:
        return f"{HOSTED_OPENAI_ENABLED_ENV_VAR} is not enabled"
    if not config.base_url:
        return f"missing required env var: {HOSTED_OPENAI_BASE_URL_ENV_VAR}"
    if not config.model:
        return f"missing required env var: {HOSTED_OPENAI_MODEL_ENV_VAR}"
    if not config.api_key:
        return f"missing required env var: {HOSTED_OPENAI_API_KEY_ENV_VAR}"
    return "configured"


def is_available(config: HostedOpenAICompatibleConfig) -> bool:
    return availability_reason(config) == "configured"


def _parse_bool(raw: str) -> bool:
    return raw.strip().lower() in {"1", "true", "yes", "on"}
