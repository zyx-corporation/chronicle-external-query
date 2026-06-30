from __future__ import annotations

from dataclasses import dataclass

from chronicle_external_query.plugins.contracts import (
    ProviderPluginProtocol,
    ProviderPluginStatus,
    ProviderPluginUnavailableError,
)
from chronicle_external_query.plugins.openai_compatible_hosted.answer_generator import (
    HostedOpenAICompatibleAnswerGenerator,
)
from chronicle_external_query.plugins.openai_compatible_hosted.config import (
    availability_reason,
    describe_configuration_fields,
    is_available,
    load_config_from_env,
)
from chronicle_external_query.runtime.contracts import AnswerGeneratorProtocol


@dataclass(frozen=True)
class OpenAICompatibleHostedPlugin(ProviderPluginProtocol):
    plugin_name: str = "openai-compatible-hosted"

    def is_available(self) -> bool:
        return is_available(load_config_from_env())

    def availability_reason(self) -> str:
        return availability_reason(load_config_from_env())

    def describe_configuration(self):
        return describe_configuration_fields()

    def describe_metadata(self) -> dict[str, object]:
        return {
            "credential_mode": "env_only",
            "provider_family": "hosted_llm",
            "runtime_integration": "answer_generation_enabled",
            "supports_answer_generation": True,
            "hosting_mode": "hosted",
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
        return HostedOpenAICompatibleAnswerGenerator(config=config)


def build_plugin() -> OpenAICompatibleHostedPlugin:
    return OpenAICompatibleHostedPlugin()
