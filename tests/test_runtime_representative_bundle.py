from __future__ import annotations

import json
from pathlib import Path

from chronicle_external_query.evaluation.artifacts import (
    build_evaluation_artifact,
    compare_evaluation_artifacts,
    render_markdown_comparison_report,
    render_markdown_trial_report,
)
from chronicle_external_query.retrieval.vector_adapter import load_static_vector_retriever
from chronicle_external_query.runtime.answer_runtime import AnswerRuntime


REPRESENTATIVE_FIXTURE_BUNDLE_DIR = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "query_engine_bundle"
    / "representative_cli_bundle"
)
REPRESENTATIVE_VECTOR_FIXTURE = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "vector_matches"
    / "representative-vector-matches.json"
)


def _load_graph_payload() -> dict:
    return json.loads((REPRESENTATIVE_FIXTURE_BUNDLE_DIR / "graph.json").read_text(encoding="utf-8"))


def _bundle_summary() -> dict:
    manifest = json.loads((REPRESENTATIVE_FIXTURE_BUNDLE_DIR / "bundle_manifest.json").read_text(encoding="utf-8"))
    graph = json.loads((REPRESENTATIVE_FIXTURE_BUNDLE_DIR / "graph.json").read_text(encoding="utf-8"))
    handoff = json.loads((REPRESENTATIVE_FIXTURE_BUNDLE_DIR / "query_engine_handoff.json").read_text(encoding="utf-8"))
    skeleton = json.loads((REPRESENTATIVE_FIXTURE_BUNDLE_DIR / "query_engine_adapter_skeleton.json").read_text(encoding="utf-8"))
    return {
        "bundle_dir": str(REPRESENTATIVE_FIXTURE_BUNDLE_DIR),
        "bundle_kind": manifest["bundle_kind"],
        "contract_versions": {
            "bundle_manifest": manifest["contract_version"],
            "handoff": handoff["contract_version"],
            "graph_export": graph["export_contract"]["contract_version"],
            "adapter_skeleton": skeleton["contract_version"],
        },
        "primary_record_path": manifest["primary_record_path"],
        "primary_record_present": True,
        "import_ready": manifest["import_ready"],
        "import_validation_status": manifest["import_validation_status"],
        "graph_stats": {
            "node_count": len(graph["nodes"]),
            "edge_count": len(graph["edges"]),
        },
    }


def test_answer_runtime_handles_representative_graph_query():
    answer = AnswerRuntime().answer(_load_graph_payload(), query="release planning follow-up context")

    assert answer.status == "answered"
    assert answer.metadata["retrieval_mode"] == "graph-only"
    assert answer.metadata["match_count"] == 4
    assert answer.metadata["top_match_source_record_ids"] == [
        "evt_context_release_planning",
        "ctx_release_planning",
        "evt_context_incident_follow_up",
    ]
    assert "4 additional" not in answer.answer_text
    assert "3 additional supporting matches available" in answer.answer_text


def test_answer_runtime_handles_representative_hybrid_query():
    answer = AnswerRuntime(
        mode="hybrid",
        vector_retriever=load_static_vector_retriever(REPRESENTATIVE_VECTOR_FIXTURE),
    ).answer(_load_graph_payload(), query="release planning follow-up context")

    assert answer.status == "answered"
    assert answer.metadata["retrieval_mode"] == "hybrid"
    assert answer.metadata["match_count"] == 5
    assert answer.metadata["overlap_source_record_ids"] == ["ctx_release_planning"]
    assert answer.metadata["top_match_sources"] == ["graph", "hybrid_overlap", "graph"]


def test_evaluation_artifacts_are_comparable_across_repeated_runs_for_same_query():
    runtime = AnswerRuntime()
    first = build_evaluation_artifact(
        runtime.answer(_load_graph_payload(), query="release planning follow-up context"),
        bundle_summary=_bundle_summary(),
    )
    second = build_evaluation_artifact(
        runtime.answer(_load_graph_payload(), query="release planning follow-up context"),
        bundle_summary=_bundle_summary(),
    )

    comparison = compare_evaluation_artifacts(first, second)

    assert comparison["query_matches"] is True
    assert comparison["runtime_status_changed"] is False
    assert comparison["retrieval_mode_changed"] is False
    assert comparison["sufficiency_changed"] is False
    assert comparison["match_count_delta"] == 0
    assert comparison["bundle_summary_changed"] is False
    assert comparison["contract_versions_changed"] is False
    assert comparison["graph_stats_changed"] is False


def test_markdown_reports_preserve_representative_hybrid_review_context():
    answer = AnswerRuntime(
        mode="hybrid",
        vector_retriever=load_static_vector_retriever(REPRESENTATIVE_VECTOR_FIXTURE),
    ).answer(_load_graph_payload(), query="release planning follow-up context")
    artifact = build_evaluation_artifact(
        answer,
        reviewer="runtime-reviewer",
        downstream_consumer="representative-consumer",
        files_reviewed=["query_engine_handoff.json", "graph.json", "bundle_manifest.json"],
        bundle_summary=_bundle_summary(),
    )

    markdown = render_markdown_trial_report(artifact)

    assert "- Reviewer: runtime-reviewer" in markdown
    assert "- Retrieval mode observed: hybrid" in markdown
    assert "- Source match counts observed: graph=4, vector=2, merged=5" in markdown
    assert "- Overlap source record ids observed: `ctx_release_planning`" in markdown


def test_markdown_comparison_report_surfaces_representative_runtime_delta():
    graph_artifact = build_evaluation_artifact(
        AnswerRuntime().answer(_load_graph_payload(), query="release planning follow-up context"),
        bundle_summary=_bundle_summary(),
    )
    hybrid_artifact = build_evaluation_artifact(
        AnswerRuntime(
            mode="hybrid",
            vector_retriever=load_static_vector_retriever(REPRESENTATIVE_VECTOR_FIXTURE),
        ).answer(_load_graph_payload(), query="release planning follow-up context"),
        bundle_summary=_bundle_summary(),
    )

    markdown = render_markdown_comparison_report(graph_artifact, hybrid_artifact)

    assert "- Retrieval mode changed: True" in markdown
    assert "- Match count delta: 1" in markdown
    assert "- Left source match counts: graph=4" in markdown
    assert "- Right source match counts: graph=4, vector=2, merged=5" in markdown
