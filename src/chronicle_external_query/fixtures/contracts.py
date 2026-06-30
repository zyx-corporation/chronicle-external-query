from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class FixtureSet:
    fixture_id: str
    source_name: str
    fixture_kind: str
    bundle_dir: Path
    vector_fixture_path: Path | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    is_baseline: bool = False


class FixtureSourceProtocol(Protocol):
    source_name: str

    def list_fixture_sets(self) -> list[FixtureSet]:
        ...

    def load_fixture_set(self, fixture_id: str) -> FixtureSet:
        ...


class FixtureRegistryError(ValueError):
    """Raised when fixture registry configuration is invalid."""
