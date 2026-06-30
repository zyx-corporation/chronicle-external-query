from __future__ import annotations

from pathlib import Path

import pytest

from chronicle_external_query.evaluation.artifacts import (
    build_chronicle_trial_alignment,
    build_evaluation_artifact,
    compare_evaluation_artifacts,
    load_evaluation_artifact,
    render_markdown_comparison_report,
    render_markdown_trial_report,
    save_evaluation_artifact,
)
from chronicle_external_query.models import EvaluationArtifactValidationError
from chronicle_external_query.runtime.answer_runtime import AnswerRuntime


def test_build_evaluation_artifact_exposes_reviewable_fields():
    graph_payload = {
        "nodes": [
            {"node_id": "n_evt_1", "source_id": "evt_1", "node_type": "event", "title": "Chronicle graph bundle"},
        ],
        "edges": [],
    }

    answer = AnswerRuntime().answer(graph_payload, query="chronicle graph")
    artifact = build_evaluation_artifact(
        answer,
        bundle_summary={
            "bundle_kind": "query_engine_handoff_bundle",
            "primary_record_path": ".chronicle/chronicle.jsonl",
            "graph_stats": {"node_count": 1, "edge_count": 0},
        },
    )

    assert artifact.artifact_version == "1.0"
    assert artifact.runtime_status == "answered"
    assert artifact.retrieval_mode == "graph-only"
    assert artifact.sufficient is True
    assert artifact.bundle_summary["bundle_kind"] == "query_engine_handoff_bundle"
    assert artifact.matches[0]["source_record_id"] == "evt_1"


def test_compare_evaluation_artifacts_surfaces_meaningful_deltas():
    empty_graph_payload = {"nodes": [], "edges": []}
    rich_graph_payload = {
        "nodes": [
            {"node_id": "n_evt_1", "source_id": "evt_1", "node_type": "event", "title": "Chronicle graph bundle"},
        ],
        "edges": [],
    }

    left = build_evaluation_artifact(
        AnswerRuntime().answer(empty_graph_payload, query="chronicle graph"),
        bundle_summary={
            "bundle_kind": "query_engine_handoff_bundle",
            "primary_record_path": ".chronicle/chronicle.jsonl",
            "contract_versions": {"handoff": "1.0"},
            "graph_stats": {"node_count": 0, "edge_count": 0},
        },
    )
    right = build_evaluation_artifact(
        AnswerRuntime().answer(rich_graph_payload, query="chronicle graph"),
        bundle_summary={
            "bundle_kind": "query_engine_handoff_bundle",
            "primary_record_path": ".chronicle/chronicle.jsonl",
            "contract_versions": {"handoff": "1.0"},
            "graph_stats": {"node_count": 1, "edge_count": 0},
        },
    )
    comparison = compare_evaluation_artifacts(left, right)

    assert comparison["query_matches"] is True
    assert comparison["runtime_status_changed"] is True
    assert comparison["sufficiency_changed"] is True
    assert comparison["match_count_delta"] == 1
    assert comparison["bundle_summary_changed"] is True
    assert comparison["graph_stats_changed"] is True
    assert comparison["contract_versions_changed"] is False


def test_compare_evaluation_artifacts_surfaces_bundle_identity_deltas():
    graph_payload = {"nodes": [], "edges": []}

    left = build_evaluation_artifact(
        AnswerRuntime().answer(graph_payload, query="chronicle graph"),
        bundle_summary={
            "bundle_kind": "query_engine_handoff_bundle",
            "primary_record_path": ".chronicle/chronicle.jsonl",
            "contract_versions": {"handoff": "1.0", "graph_export": "1.0"},
            "graph_stats": {"node_count": 0, "edge_count": 0},
        },
    )
    right = build_evaluation_artifact(
        AnswerRuntime().answer(graph_payload, query="chronicle graph"),
        bundle_summary={
            "bundle_kind": "query_engine_handoff_bundle_v2",
            "primary_record_path": ".chronicle/alt.jsonl",
            "contract_versions": {"handoff": "1.1", "graph_export": "1.0"},
            "graph_stats": {"node_count": 0, "edge_count": 0},
        },
    )

    comparison = compare_evaluation_artifacts(left, right)

    assert comparison["bundle_summary_changed"] is True
    assert comparison["bundle_kind_changed"] is True
    assert comparison["primary_record_path_changed"] is True
    assert comparison["contract_versions_changed"] is True


def test_save_and_load_evaluation_artifact_round_trip(tmp_path: Path):
    graph_payload = {
        "nodes": [
            {"node_id": "n_evt_1", "source_id": "evt_1", "node_type": "event", "title": "Chronicle graph bundle"},
        ],
        "edges": [],
    }
    artifact = build_evaluation_artifact(
        AnswerRuntime().answer(graph_payload, query="chronicle graph"),
        reviewer="tester",
        downstream_consumer="demo-consumer",
        files_reviewed=["graph.json", "query_engine_handoff.json"],
        bundle_summary={
            "bundle_kind": "query_engine_handoff_bundle",
            "primary_record_path": ".chronicle/chronicle.jsonl",
            "graph_stats": {"node_count": 1, "edge_count": 0},
        },
    )
    output_path = tmp_path / "artifact.json"

    save_evaluation_artifact(artifact, output_path)
    loaded = load_evaluation_artifact(output_path)

    assert loaded.reviewer == "tester"
    assert loaded.downstream_consumer == "demo-consumer"
    assert loaded.files_reviewed == ["graph.json", "query_engine_handoff.json"]
    assert loaded.bundle_summary["bundle_kind"] == "query_engine_handoff_bundle"


def test_load_evaluation_artifact_rejects_missing_file(tmp_path: Path):
    missing_path = tmp_path / "missing-artifact.json"

    with pytest.raises(EvaluationArtifactValidationError, match="file was not found"):
        load_evaluation_artifact(missing_path)


def test_load_evaluation_artifact_rejects_invalid_root_shape(tmp_path: Path):
    artifact_path = tmp_path / "invalid-root.json"
    artifact_path.write_text('["not", "an", "object"]', encoding="utf-8")

    with pytest.raises(EvaluationArtifactValidationError, match="must decode to an object"):
        load_evaluation_artifact(artifact_path)


def test_load_evaluation_artifact_rejects_invalid_json(tmp_path: Path):
    artifact_path = tmp_path / "invalid-json.json"
    artifact_path.write_text("{invalid json", encoding="utf-8")

    with pytest.raises(EvaluationArtifactValidationError, match="contains invalid JSON"):
        load_evaluation_artifact(artifact_path)


def test_load_evaluation_artifact_rejects_missing_required_keys(tmp_path: Path):
    artifact_path = tmp_path / "missing-keys.json"
    artifact_path.write_text(
        '{"artifact_version":"1.0","query":"fixture bundle"}',
        encoding="utf-8",
    )

    with pytest.raises(EvaluationArtifactValidationError, match="missing required keys"):
        load_evaluation_artifact(artifact_path)


def test_load_evaluation_artifact_rejects_invalid_files_reviewed_shape(tmp_path: Path):
    artifact_path = tmp_path / "invalid-files-reviewed.json"
    artifact_path.write_text(
        (
            '{"artifact_version":"1.0","query":"fixture bundle","runtime_status":"answered",'
            '"retrieval_mode":"graph-only","answer_text":"ok","sufficient":true,'
            '"files_reviewed":{"graph.json":true}}'
        ),
        encoding="utf-8",
    )

    with pytest.raises(EvaluationArtifactValidationError, match="field files_reviewed must decode to a list"):
        load_evaluation_artifact(artifact_path)


def test_load_evaluation_artifact_rejects_invalid_bundle_summary_shape(tmp_path: Path):
    artifact_path = tmp_path / "invalid-bundle-summary.json"
    artifact_path.write_text(
        (
            '{"artifact_version":"1.0","query":"fixture bundle","runtime_status":"answered",'
            '"retrieval_mode":"graph-only","answer_text":"ok","sufficient":true,'
            '"bundle_summary":["not","an","object"]}'
        ),
        encoding="utf-8",
    )

    with pytest.raises(EvaluationArtifactValidationError, match="field bundle_summary must decode to an object"):
        load_evaluation_artifact(artifact_path)


def test_load_evaluation_artifact_rejects_invalid_metadata_shape(tmp_path: Path):
    artifact_path = tmp_path / "invalid-metadata.json"
    artifact_path.write_text(
        (
            '{"artifact_version":"1.0","query":"fixture bundle","runtime_status":"answered",'
            '"retrieval_mode":"graph-only","answer_text":"ok","sufficient":true,'
            '"metadata":["not","an","object"]}'
        ),
        encoding="utf-8",
    )

    with pytest.raises(EvaluationArtifactValidationError, match="field metadata must decode to an object"):
        load_evaluation_artifact(artifact_path)


def test_load_evaluation_artifact_rejects_invalid_provenance_shape(tmp_path: Path):
    artifact_path = tmp_path / "invalid-provenance.json"
    artifact_path.write_text(
        (
            '{"artifact_version":"1.0","query":"fixture bundle","runtime_status":"answered",'
            '"retrieval_mode":"graph-only","answer_text":"ok","sufficient":true,'
            '"provenance":["not","an","object"]}'
        ),
        encoding="utf-8",
    )

    with pytest.raises(EvaluationArtifactValidationError, match="field provenance must decode to an object"):
        load_evaluation_artifact(artifact_path)


def test_load_evaluation_artifact_rejects_invalid_matches_shape(tmp_path: Path):
    artifact_path = tmp_path / "invalid-matches.json"
    artifact_path.write_text(
        (
            '{"artifact_version":"1.0","query":"fixture bundle","runtime_status":"answered",'
            '"retrieval_mode":"graph-only","answer_text":"ok","sufficient":true,'
            '"matches":{"evt_1":true}}'
        ),
        encoding="utf-8",
    )

    with pytest.raises(EvaluationArtifactValidationError, match="field matches must decode to a list"):
        load_evaluation_artifact(artifact_path)


def test_load_evaluation_artifact_rejects_non_string_files_reviewed_entry(tmp_path: Path):
    artifact_path = tmp_path / "invalid-files-reviewed-entry.json"
    artifact_path.write_text(
        (
            '{"artifact_version":"1.0","query":"fixture bundle","runtime_status":"answered",'
            '"retrieval_mode":"graph-only","answer_text":"ok","sufficient":true,'
            '"files_reviewed":["graph.json", 3]}'
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        EvaluationArtifactValidationError,
        match="field files_reviewed entry 1 must decode to a string",
    ):
        load_evaluation_artifact(artifact_path)


def test_load_evaluation_artifact_rejects_non_object_matches_entry(tmp_path: Path):
    artifact_path = tmp_path / "invalid-matches-entry.json"
    artifact_path.write_text(
        (
            '{"artifact_version":"1.0","query":"fixture bundle","runtime_status":"answered",'
            '"retrieval_mode":"graph-only","answer_text":"ok","sufficient":true,'
            '"matches":[{"identifier":"evt_1"}, "bad-entry"]}'
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        EvaluationArtifactValidationError,
        match="field matches entry 1 must decode to an object",
    ):
        load_evaluation_artifact(artifact_path)


def test_build_chronicle_trial_alignment_matches_trial_review_shape():
    graph_payload = {"nodes": [], "edges": []}
    artifact = build_evaluation_artifact(
        AnswerRuntime().answer(graph_payload, query="chronicle graph"),
        reviewer="tester",
        downstream_consumer="demo-consumer",
    )

    alignment = build_chronicle_trial_alignment(artifact)

    assert alignment["record_kind"] == "query_engine_bundle_trial"
    assert alignment["reviewer"] == "tester"
    assert alignment["downstream_consumer"] == "demo-consumer"
    assert alignment["sufficient"] is False
    assert "missing behavior:" in alignment["missing_behavior"]


def test_render_markdown_trial_report_uses_artifact_fields():
    graph_payload = {
        "nodes": [
            {"node_id": "n_evt_1", "source_id": "evt_1", "node_type": "event", "title": "Chronicle graph bundle"},
        ],
        "edges": [],
    }
    artifact = build_evaluation_artifact(
        AnswerRuntime().answer(graph_payload, query="chronicle graph"),
        reviewer="tester",
        downstream_consumer="demo-consumer",
        files_reviewed=["graph.json", "bundle_manifest.json"],
        bundle_summary={
            "bundle_kind": "query_engine_handoff_bundle",
            "primary_record_path": ".chronicle/chronicle.jsonl",
            "contract_versions": {
                "bundle_manifest": "1.0",
                "handoff": "1.0",
            },
            "graph_stats": {"node_count": 1, "edge_count": 0},
        },
    )

    markdown = render_markdown_trial_report(artifact)

    assert "# Query-Engine Handoff Bundle Trial Report" in markdown
    assert "- Reviewer: tester" in markdown
    assert "- Bundle kind: query_engine_handoff_bundle" in markdown
    assert "## Bundle contract versions" in markdown
    assert "- `bundle_manifest`: `1.0`" in markdown
    assert "- Source match counts observed: graph=1" in markdown
    assert "- Overlap source record ids observed: (none)" in markdown
    assert "- [x] `graph.json`" in markdown
    assert "- [x] Bundle was sufficient for downstream trial" in markdown


def test_render_markdown_comparison_report_surfaces_comparison_summary():
    left = build_evaluation_artifact(
        AnswerRuntime().answer({"nodes": [], "edges": []}, query="chronicle graph"),
        bundle_summary={
            "bundle_kind": "query_engine_handoff_bundle",
            "primary_record_path": ".chronicle/chronicle.jsonl",
            "graph_stats": {"node_count": 0, "edge_count": 0},
        },
    )
    right = build_evaluation_artifact(
        AnswerRuntime().answer(
            {
                "nodes": [
                    {
                        "node_id": "n_evt_1",
                        "source_id": "evt_1",
                        "node_type": "event",
                        "title": "Chronicle graph bundle",
                    },
                ],
                "edges": [],
            },
            query="chronicle graph",
        ),
        bundle_summary={
            "bundle_kind": "query_engine_handoff_bundle",
            "primary_record_path": ".chronicle/chronicle-v2.jsonl",
            "graph_stats": {"node_count": 1, "edge_count": 0},
        },
    )

    markdown = render_markdown_comparison_report(left, right)

    assert "# Query-Engine Handoff Bundle Comparison Report" in markdown
    assert "- Runtime status changed: True" in markdown
    assert "## Retrieval provenance" in markdown
    assert "- Left source match counts: graph=0" in markdown
    assert "- Right source match counts: graph=1" in markdown
    assert "- Left insufficiency reasons: no_graph_matches" in markdown
    assert "- Right insufficiency reasons: (none)" in markdown
    assert "- Graph stats changed: True" in markdown
    assert "- Right primary record path: .chronicle/chronicle-v2.jsonl" in markdown
