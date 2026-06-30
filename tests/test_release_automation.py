from __future__ import annotations

from pathlib import Path

from chronicle_external_query.release import (
    build_plugin_compatibility_report,
    build_release_notes,
)


REPO_ROOT = Path(__file__).resolve().parent.parent


def test_build_release_notes_includes_boundary_and_roadmap_snapshot():
    notes = build_release_notes(
        version="v0.3.0-rc1",
        release_date="2026-06-30",
        repo_root=REPO_ROOT,
    )

    assert "# v0.3.0-rc1" in notes
    assert "deterministic local smoke remains the primary release gate" in notes
    assert "Milestone I" in notes
    assert "openai-compatible-hosted" in notes


def test_build_plugin_compatibility_report_marks_unconfigured_plugins_as_skipped(monkeypatch):
    monkeypatch.delenv("GEMMA4_ENABLED", raising=False)
    monkeypatch.delenv("OPENAI_COMPATIBLE_HOSTED_ENABLED", raising=False)
    monkeypatch.delenv("CHRONICLE_EXTERNAL_QUERY_STATIC_TEST_PROVIDER_API_KEY", raising=False)

    payload = build_plugin_compatibility_report()

    assert payload["plugin_count"] >= 3
    assert "gemma4" in payload["skipped_plugins"]
    assert "openai-compatible-hosted" in payload["skipped_plugins"]
