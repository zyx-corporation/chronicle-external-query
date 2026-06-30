from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class ProviderConfigurationField:
    key: str
    env_var: str
    required: bool
    secret: bool
    description: str


@dataclass(frozen=True)
class ProviderPluginStatus:
    plugin_name: str
    available: bool
    availability_reason: str
    config_fields: tuple[ProviderConfigurationField, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)


class ProviderPluginProtocol(Protocol):
    plugin_name: str

    def is_available(self) -> bool:
        ...

    def availability_reason(self) -> str:
        ...

    def describe_configuration(self) -> tuple[ProviderConfigurationField, ...]:
        ...

    def describe_metadata(self) -> dict[str, Any]:
        ...

    def describe_status(self) -> ProviderPluginStatus:
        ...


class ProviderPluginError(ValueError):
    """Raised when provider plugin loading or configuration fails."""


class ProviderPluginLoadError(ProviderPluginError):
    """Raised when a provider plugin cannot be loaded safely."""


class ProviderPluginNotFoundError(ProviderPluginLoadError):
    """Raised when an unknown provider plugin is requested."""
