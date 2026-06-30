from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module

from .contracts import (
    ProviderPluginLoadError,
    ProviderPluginNotFoundError,
    ProviderPluginProtocol,
    ProviderPluginStatus,
)


BUILTIN_PROVIDER_PLUGIN_MODULES: dict[str, str] = {
    "gemma4": "chronicle_external_query.plugins.providers.gemma4_local",
    "openai-compatible-hosted": "chronicle_external_query.plugins.providers.openai_compatible_hosted",
    "static-test-provider": "chronicle_external_query.plugins.providers.static_test_provider",
}


@dataclass(frozen=True)
class ProviderPluginDefinition:
    plugin_name: str
    module_path: str


def list_provider_plugin_definitions() -> list[ProviderPluginDefinition]:
    return [
        ProviderPluginDefinition(plugin_name=name, module_path=module_path)
        for name, module_path in sorted(BUILTIN_PROVIDER_PLUGIN_MODULES.items())
    ]


def load_provider_plugin(plugin_name: str) -> ProviderPluginProtocol:
    definition = _resolve_definition(plugin_name)
    try:
        module = import_module(definition.module_path)
    except ImportError as exc:
        raise ProviderPluginLoadError(
            f"provider plugin import failed for {plugin_name}: {definition.module_path}"
        ) from exc

    factory = getattr(module, "build_plugin", None)
    if not callable(factory):
        raise ProviderPluginLoadError(
            f"provider plugin module must expose build_plugin(): {definition.module_path}"
        )

    plugin = factory()
    if getattr(plugin, "plugin_name", "") != definition.plugin_name:
        raise ProviderPluginLoadError(
            f"provider plugin returned unexpected plugin_name: {definition.plugin_name}"
        )
    return plugin


def list_provider_plugin_statuses() -> list[ProviderPluginStatus]:
    statuses: list[ProviderPluginStatus] = []
    for definition in list_provider_plugin_definitions():
        plugin = load_provider_plugin(definition.plugin_name)
        statuses.append(plugin.describe_status())
    return statuses


def _resolve_definition(plugin_name: str) -> ProviderPluginDefinition:
    module_path = BUILTIN_PROVIDER_PLUGIN_MODULES.get(plugin_name)
    if module_path is None:
        raise ProviderPluginNotFoundError(
            f"provider plugin is not registered: {plugin_name}"
        )
    return ProviderPluginDefinition(plugin_name=plugin_name, module_path=module_path)
