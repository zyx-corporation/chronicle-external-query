from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from chronicle_external_query.plugins import list_provider_plugin_statuses


@dataclass(frozen=True)
class PluginCompatibilityEntry:
    plugin_name: str
    status: str
    availability_reason: str
    hosting_mode: str
    supports_answer_generation: bool
    credential_mode: str


def build_plugin_compatibility_report() -> dict[str, Any]:
    statuses = list_provider_plugin_statuses()
    entries: list[PluginCompatibilityEntry] = []
    for status in statuses:
        metadata = status.metadata
        entries.append(
            PluginCompatibilityEntry(
                plugin_name=status.plugin_name,
                status="configured" if status.available else "skipped",
                availability_reason=status.availability_reason,
                hosting_mode=str(metadata.get("hosting_mode", "local")),
                supports_answer_generation=bool(metadata.get("supports_answer_generation", False)),
                credential_mode=str(metadata.get("credential_mode", "unspecified")),
            )
        )

    configured_plugins = [entry.plugin_name for entry in entries if entry.status == "configured"]
    skipped_plugins = [entry.plugin_name for entry in entries if entry.status == "skipped"]
    return {
        "plugin_count": len(entries),
        "configured_plugins": configured_plugins,
        "skipped_plugins": skipped_plugins,
        "entries": [asdict(entry) for entry in entries],
    }
