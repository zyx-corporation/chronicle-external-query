from __future__ import annotations

from dataclasses import dataclass

from chronicle_external_query.plugins.contracts import (
    ProviderPluginProtocol,
    ProviderPluginUnavailableError,
    ProviderPluginStatus,
)
from chronicle_external_query.plugins.gemma4.answer_generator import Gemma4AnswerGenerator
from chronicle_external_query.plugins.gemma4.config import (
    availability_reason,
    describe_configuration_fields,
    is_available,
    load_config_from_env,
)
from chronicle_external_query.runtime.contracts import AnswerGeneratorProtocol


@dataclass(frozen=True)
class Gemma4LocalPlugin(ProviderPluginProtocol):
    plugin_name: str = "gemma4"

    def is_available(self) -> bool:
        return is_available(load_config_from_env())

    def availability_reason(self) -> str:
        return availability_reason(load_config_from_env())

    def describe_configuration(self):
        return describe_configuration_fields()

    def describe_metadata(self) -> dict[str, object]:
        return {
            "credential_mode": "env_only",
            "hosting_mode": "local",
            "provider_family": "local_llm",
            "runtime_integration": "answer_generation_enabled",
            "supports_answer_generation": True,
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
        config = load_config_from_env()
        if not is_available(config):
            raise ProviderPluginUnavailableError(self.availability_reason())
        return Gemma4AnswerGenerator(config=config)


def build_plugin() -> Gemma4LocalPlugin:
    return Gemma4LocalPlugin()
