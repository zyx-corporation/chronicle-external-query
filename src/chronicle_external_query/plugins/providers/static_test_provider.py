from __future__ import annotations

import os
from dataclasses import dataclass

from chronicle_external_query.plugins.contracts import (
    ProviderConfigurationField,
    ProviderPluginProtocol,
    ProviderPluginUnavailableError,
    ProviderPluginStatus,
)
from chronicle_external_query.runtime.contracts import AnswerGeneratorProtocol


API_KEY_ENV_VAR = "CHRONICLE_EXTERNAL_QUERY_STATIC_TEST_PROVIDER_API_KEY"
ENDPOINT_ENV_VAR = "CHRONICLE_EXTERNAL_QUERY_STATIC_TEST_PROVIDER_ENDPOINT"


@dataclass(frozen=True)
class StaticTestProviderPlugin(ProviderPluginProtocol):
    plugin_name: str = "static-test-provider"

    def is_available(self) -> bool:
        return bool(os.getenv(API_KEY_ENV_VAR, "").strip())

    def availability_reason(self) -> str:
        if self.is_available():
            return "configured"
        return f"missing required credential env var: {API_KEY_ENV_VAR}"

    def describe_configuration(self) -> tuple[ProviderConfigurationField, ...]:
        return (
            ProviderConfigurationField(
                key="api_key",
                env_var=API_KEY_ENV_VAR,
                required=True,
                secret=True,
                description="API key for the opt-in static provider integration.",
            ),
            ProviderConfigurationField(
                key="endpoint",
                env_var=ENDPOINT_ENV_VAR,
                required=False,
                secret=False,
                description="Optional explicit provider endpoint override.",
            ),
        )

    def describe_metadata(self) -> dict[str, object]:
        return {
            "credential_mode": "env_only",
            "provider_family": "test_provider",
            "runtime_integration": "reserved_only",
        }

    def describe_status(self) -> ProviderPluginStatus:
        return ProviderPluginStatus(
            plugin_name=self.plugin_name,
            available=self.is_available(),
            availability_reason=self.availability_reason(),
            config_fields=self.describe_configuration(),
            metadata=self.describe_metadata(),
        )

    def build_answer_generator(self) -> AnswerGeneratorProtocol:
        raise ProviderPluginUnavailableError(
            f"{self.plugin_name} does not provide answer generation in Milestone H"
        )


def build_plugin() -> StaticTestProviderPlugin:
    return StaticTestProviderPlugin()
