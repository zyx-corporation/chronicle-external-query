from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import FixtureRegistryError, FixtureSet, FixtureSourceProtocol


FIXTURE_PACK_ENV_VAR = "CHRONICLE_EXTERNAL_QUERY_FIXTURE_DIRS"
FIXTURE_PACK_MANIFEST = "fixture-pack.json"


@dataclass(frozen=True)
class _ManifestFixtureSource:
    manifest_path: Path
    source_name: str

    def list_fixture_sets(self) -> list[FixtureSet]:
        payload = _load_manifest_payload(self.manifest_path)
        fixtures = payload.get("fixtures")
        if not isinstance(fixtures, list):
            raise FixtureRegistryError(
                f"fixture pack manifest must contain a fixtures list: {self.manifest_path}"
            )

        manifest_dir = self.manifest_path.parent
        fixture_sets: list[FixtureSet] = []
        for entry in fixtures:
            fixture_sets.append(_build_manifest_fixture_set(entry=entry, manifest_dir=manifest_dir, source_name=self.source_name))
        return fixture_sets

    def load_fixture_set(self, fixture_id: str) -> FixtureSet:
        for fixture_set in self.list_fixture_sets():
            if fixture_set.fixture_id == fixture_id:
                return fixture_set
        raise FixtureRegistryError(
            f"fixture id was not found in fixture pack {self.source_name}: {fixture_id}"
        )


@dataclass(frozen=True)
class _StaticFixtureSource:
    source_name: str
    fixture_sets: tuple[FixtureSet, ...]

    def list_fixture_sets(self) -> list[FixtureSet]:
        return list(self.fixture_sets)

    def load_fixture_set(self, fixture_id: str) -> FixtureSet:
        for fixture_set in self.fixture_sets:
            if fixture_set.fixture_id == fixture_id:
                return fixture_set
        raise FixtureRegistryError(
            f"fixture id was not found in fixture source {self.source_name}: {fixture_id}"
        )


class FixtureRegistry:
    def __init__(self, sources: list[FixtureSourceProtocol]):
        self._sources = sources

    @classmethod
    def default(
        cls,
        *,
        repo_root: Path | None = None,
        fixture_dirs: list[Path] | None = None,
        include_env_fixture_dirs: bool = True,
    ) -> "FixtureRegistry":
        root = repo_root or _default_repo_root()
        sources: list[FixtureSourceProtocol] = [_build_baseline_fixture_source(root)]

        optional_dirs: list[Path] = []
        if include_env_fixture_dirs:
            optional_dirs.extend(_parse_fixture_dirs_env())
        if fixture_dirs:
            optional_dirs.extend(fixture_dirs)

        for fixture_dir in optional_dirs:
            sources.append(load_fixture_source_from_dir(fixture_dir))
        return cls(sources=sources)

    def list_fixture_sets(self) -> list[FixtureSet]:
        fixture_sets: list[FixtureSet] = []
        seen_ids: set[str] = set()

        for source in self._sources:
            for fixture_set in source.list_fixture_sets():
                if fixture_set.fixture_id in seen_ids:
                    raise FixtureRegistryError(
                        f"duplicate fixture id discovered across registry sources: {fixture_set.fixture_id}"
                    )
                seen_ids.add(fixture_set.fixture_id)
                fixture_sets.append(fixture_set)
        return fixture_sets

    def load_fixture_set(self, fixture_id: str) -> FixtureSet:
        for source in self._sources:
            try:
                return source.load_fixture_set(fixture_id)
            except FixtureRegistryError:
                continue
        raise FixtureRegistryError(f"fixture id was not found in registry: {fixture_id}")


def load_fixture_source_from_dir(fixture_dir: Path) -> FixtureSourceProtocol:
    manifest_path = fixture_dir / FIXTURE_PACK_MANIFEST
    if not manifest_path.exists():
        raise FixtureRegistryError(
            f"fixture pack manifest was not found: {manifest_path}"
        )

    payload = _load_manifest_payload(manifest_path)
    source_name = payload.get("source_name")
    if not isinstance(source_name, str) or not source_name.strip():
        raise FixtureRegistryError(
            f"fixture pack manifest must include a non-empty source_name: {manifest_path}"
        )
    return _ManifestFixtureSource(manifest_path=manifest_path, source_name=source_name.strip())


def _build_baseline_fixture_source(repo_root: Path) -> FixtureSourceProtocol:
    tests_dir = repo_root / "tests" / "fixtures"
    return _StaticFixtureSource(
        source_name="baseline_repo_fixtures",
        fixture_sets=(
            FixtureSet(
                fixture_id="baseline_minimal",
                source_name="baseline_repo_fixtures",
                fixture_kind="baseline_minimal",
                bundle_dir=tests_dir / "query_engine_bundle" / "minimal_cli_bundle",
                vector_fixture_path=tests_dir / "vector_matches" / "sample-vector-matches.json",
                metadata={
                    "origin": "real Chronicle CLI generated bundle reduced for deterministic testing",
                    "sanitization_status": "minimal fixture with no primary Chronicle record",
                    "intended_test_scope": [
                        "bundle_validation",
                        "cli_smoke",
                        "graph_only_runtime",
                    ],
                    "default_baseline": True,
                },
                is_baseline=True,
            ),
            FixtureSet(
                fixture_id="baseline_representative",
                source_name="baseline_repo_fixtures",
                fixture_kind="baseline_representative",
                bundle_dir=tests_dir / "query_engine_bundle" / "representative_cli_bundle",
                vector_fixture_path=tests_dir / "vector_matches" / "representative-vector-matches.json",
                metadata={
                    "origin": "sanitized Chronicle-derived representative bundle",
                    "sanitization_status": "sanitized fixture with reduced Chronicle primary record copy",
                    "intended_test_scope": [
                        "representative_ingest",
                        "hybrid_retrieval_regression",
                        "runtime_regression",
                    ],
                    "default_baseline": True,
                },
                is_baseline=True,
            ),
        ),
    )


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _parse_fixture_dirs_env() -> list[Path]:
    raw = os.getenv(FIXTURE_PACK_ENV_VAR, "")
    if not raw.strip():
        return []
    return [Path(part).expanduser() for part in raw.split(os.pathsep) if part.strip()]


def _load_manifest_payload(manifest_path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise FixtureRegistryError(
            f"fixture pack manifest contains invalid JSON: {manifest_path}"
        ) from exc

    if not isinstance(payload, dict):
        raise FixtureRegistryError(
            f"fixture pack manifest must decode to an object: {manifest_path}"
        )

    manifest_version = payload.get("manifest_version")
    if manifest_version != "1.0":
        raise FixtureRegistryError(
            f"fixture pack manifest version is unsupported: {manifest_path}"
        )
    return payload


def _build_manifest_fixture_set(
    *,
    entry: Any,
    manifest_dir: Path,
    source_name: str,
) -> FixtureSet:
    if not isinstance(entry, dict):
        raise FixtureRegistryError(
            f"fixture pack entry must decode to an object: {manifest_dir / FIXTURE_PACK_MANIFEST}"
        )

    fixture_id = _require_string(entry, "fixture_id", manifest_dir)
    fixture_kind = _require_string(entry, "fixture_kind", manifest_dir)
    bundle_dir = (manifest_dir / _require_string(entry, "bundle_dir", manifest_dir)).resolve()
    if not bundle_dir.is_dir():
        raise FixtureRegistryError(f"fixture bundle directory was not found: {bundle_dir}")

    vector_fixture_path: Path | None = None
    raw_vector_fixture = entry.get("vector_fixture")
    if raw_vector_fixture is not None:
        if not isinstance(raw_vector_fixture, str) or not raw_vector_fixture.strip():
            raise FixtureRegistryError(
                f"fixture vector_fixture must be a non-empty string: {manifest_dir / FIXTURE_PACK_MANIFEST}"
            )
        vector_fixture_path = (manifest_dir / raw_vector_fixture).resolve()
        if not vector_fixture_path.exists():
            raise FixtureRegistryError(
                f"fixture vector fixture was not found: {vector_fixture_path}"
            )

    metadata = entry.get("metadata", {})
    if not isinstance(metadata, dict):
        raise FixtureRegistryError(
            f"fixture metadata must decode to an object: {manifest_dir / FIXTURE_PACK_MANIFEST}"
        )

    is_baseline = bool(entry.get("default_baseline", False))
    return FixtureSet(
        fixture_id=fixture_id,
        source_name=source_name,
        fixture_kind=fixture_kind,
        bundle_dir=bundle_dir,
        vector_fixture_path=vector_fixture_path,
        metadata=metadata,
        is_baseline=is_baseline,
    )


def _require_string(entry: dict[str, Any], key: str, manifest_dir: Path) -> str:
    value = entry.get(key)
    if not isinstance(value, str) or not value.strip():
        raise FixtureRegistryError(
            f"fixture pack entry must include a non-empty {key}: {manifest_dir / FIXTURE_PACK_MANIFEST}"
        )
    return value.strip()
