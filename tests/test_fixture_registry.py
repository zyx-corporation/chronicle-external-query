from __future__ import annotations

import os
import json
from pathlib import Path

import pytest

from chronicle_external_query.fixtures import FixtureRegistry, FixtureRegistryError


REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_ROOT = REPO_ROOT / "tests" / "fixtures"


def test_default_fixture_registry_lists_committed_baseline_fixtures():
    registry = FixtureRegistry.default(repo_root=REPO_ROOT, include_env_fixture_dirs=False)

    fixture_sets = registry.list_fixture_sets()

    assert [fixture_set.fixture_id for fixture_set in fixture_sets] == [
        "baseline_minimal",
        "baseline_representative",
    ]
    assert all(fixture_set.is_baseline for fixture_set in fixture_sets)
    assert fixture_sets[0].bundle_dir == FIXTURES_ROOT / "query_engine_bundle" / "minimal_cli_bundle"
    assert fixture_sets[1].vector_fixture_path == FIXTURES_ROOT / "vector_matches" / "representative-vector-matches.json"
    assert fixture_sets[1].metadata["sanitization_status"].startswith("sanitized fixture")


def test_fixture_registry_loads_optional_manifest_pack(tmp_path: Path):
    pack_dir = _write_fixture_pack(
        tmp_path,
        fixture_id="optional_comparison_fixture",
        fixture_kind="optional_provider_comparison_pack",
    )

    registry = FixtureRegistry.default(
        repo_root=REPO_ROOT,
        fixture_dirs=[pack_dir],
        include_env_fixture_dirs=False,
    )

    fixture_sets = registry.list_fixture_sets()

    assert [fixture_set.fixture_id for fixture_set in fixture_sets] == [
        "baseline_minimal",
        "baseline_representative",
        "optional_comparison_fixture",
    ]
    optional_fixture = registry.load_fixture_set("optional_comparison_fixture")
    assert optional_fixture.is_baseline is False
    assert optional_fixture.source_name == "temporary_pack"
    assert optional_fixture.bundle_dir == FIXTURES_ROOT / "query_engine_bundle" / "representative_cli_bundle"
    assert optional_fixture.metadata["origin"] == "sanitized Chronicle-derived fixture pack"


def test_fixture_registry_rejects_duplicate_fixture_ids(tmp_path: Path):
    pack_dir = _write_fixture_pack(
        tmp_path,
        fixture_id="baseline_minimal",
        fixture_kind="optional_provider_comparison_pack",
    )

    registry = FixtureRegistry.default(
        repo_root=REPO_ROOT,
        fixture_dirs=[pack_dir],
        include_env_fixture_dirs=False,
    )

    with pytest.raises(FixtureRegistryError) as excinfo:
        registry.list_fixture_sets()

    assert "duplicate fixture id" in str(excinfo.value)


def _write_fixture_pack(tmp_path: Path, *, fixture_id: str, fixture_kind: str) -> Path:
    pack_dir = tmp_path / "fixture-pack"
    pack_dir.mkdir()
    manifest_path = pack_dir / "fixture-pack.json"
    manifest_path.write_text(
        json.dumps(
            {
                "manifest_version": "1.0",
                "source_name": "temporary_pack",
                "fixtures": [
                    {
                        "fixture_id": fixture_id,
                        "fixture_kind": fixture_kind,
                        "bundle_dir": _relative_to_pack(
                            pack_dir,
                            FIXTURES_ROOT / "query_engine_bundle" / "representative_cli_bundle",
                        ),
                        "vector_fixture": _relative_to_pack(
                            pack_dir,
                            FIXTURES_ROOT / "vector_matches" / "representative-vector-matches.json",
                        ),
                        "metadata": {
                            "origin": "sanitized Chronicle-derived fixture pack",
                            "sanitization_status": "sanitized",
                            "intended_test_scope": ["provider_comparison"],
                        },
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return pack_dir


def _relative_to_pack(pack_dir: Path, target: Path) -> str:
    return os.path.relpath(target, start=pack_dir)
